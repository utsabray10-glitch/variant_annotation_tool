"""
Author: Utsab Ray

Created: 2025-11-17

Description:
    Module with functions to iterate over a vcf and annotate them
"""

from typing import Generator
from src.models import AnnotatedVariant, Variant
from pathlib import Path
from src.vep import make_vep_request, get_genes_for_most_severe_consequence
from src.config import VEP_REGION_PAYLOAD
from cyvcf2 import VCF


def read_vcf(input_vcf: Path) -> Generator[Variant, None, None]:
    """
    Iterate through VCF and yield instance(s) of Variant for each variant

    Args:
        input_vcf (Path): Path to the input VCF file

    Returns:
        Yield one instance of Variant
    """
    vcf = VCF(input_vcf)

    for variant in vcf:
        ao = ensure_tuple(variant.INFO["AO"])
        af = ensure_tuple(variant.INFO["AF"])
        # Even if multiple ALT alleles, variant.INFO["TYPE"] gives comma separated string of types instead of tuple
        variant_type = (
            variant.INFO["TYPE"].split(",")
            if "," in variant.INFO["TYPE"]
            else [variant.INFO["TYPE"]]
        )
        for idx, alt in enumerate(variant.ALT):
            # For multiple ALT alleles, create an annotation for each individual ALT allele
            yield Variant(
                chrom=variant.CHROM,
                pos=variant.POS,
                ref=variant.REF,
                alt=alt,
                depth=variant.INFO["DP"],
                ref_reads=variant.INFO["RO"],
                alt_reads=ao[idx],
                maf=round(min(af[idx], 1 - af[idx]), 2),
                type=variant_type[idx],
            )


def build_annotation(variant_data_batch: list[Variant]) -> list[AnnotatedVariant]:
    """
    Annotate each individual variant with info from VEP API and some additional stats

    Args:
        variant_data_batch (list[Variant]): All instances of Variant that are to be annotated

    Returns:
        List of instances of AnnotatedVariant that represents all info related to annotated variants
    """
    # Store all instances of AnnotatedVariant
    # Elements correspond one to one with @variant_data_batch
    annotated_variants = []

    # Payloads (string for that variant to query API) for all variants in @variant_data_batch
    variant_payload_batch = []

    for variant_data in variant_data_batch:
        variant_payload = VEP_REGION_PAYLOAD.format(
            chrom=variant_data.chrom,
            pos=variant_data.pos,
            ref=variant_data.ref,
            alt=variant_data.alt,
        )
        variant_payload_batch.append(variant_payload)

    # Payload to send to the API
    # Payload format retrieved from https://grch37.rest.ensembl.org/documentation/info/vep_region_post
    payload = {"variants": variant_payload_batch}
    vep_data_batch = make_vep_request(payload)

    # Iterate through all VEP data for this batch and create AnnotatedVariant instances
    for idx, vep_data in enumerate(vep_data_batch):
        annotated_variants.append(
            AnnotatedVariant(
                # Data from Variant
                **variant_data_batch[idx].model_dump(),
                gene=get_genes_for_most_severe_consequence(vep_data),
                consequence=vep_data["most_severe_consequence"],
                alt_perc=round(
                    (variant_data_batch[idx].alt_reads * 100)
                    / (
                        variant_data_batch[idx].alt_reads
                        + variant_data_batch[idx].ref_reads
                    ),
                    2,
                ),
            )
        )

    return annotated_variants


def ensure_tuple(value: tuple | int) -> tuple:
    """
    Convert single values to tuple for consistent iteration downstream

    Args:
        value (tuple|int): Convert to tuple if int to ensure downstream processing has consistent syntax

    Returns:
        Tuple
    """
    return value if isinstance(value, tuple) else (value,)
