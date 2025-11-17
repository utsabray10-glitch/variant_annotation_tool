"""
Author: Utsab Ray

Created: 2025-11-17

Description:
    Module with definitions of Pydantic models for Variant and AnnotatedVariant
"""

from pydantic import BaseModel, Field, model_validator
from typing import Literal


class Variant(BaseModel):
    """
    A variant record from a VCF file

    Attributes:
        chrom (str): Chromosome ID
        pos (int): 1-based position of the variant
        ref (str): Reference allele sequence
        alt (str): Alternate allele sequence
        depth (int): Read depth at the variant position
        ref_reads (int): Number of reads supporting the reference allele
        alt_reads (int): Number of reads supporting the alternate allele
        maf (float): Minor allele frequency (0 to 1)
        type (str): Type of variant ("snp", "ins", "del", "complex", "mnp")
    """

    chrom: str
    pos: int = Field(gt=0) # variant.POS
    ref: str = Field(pattern=r"^[ACGT]+$") # variant.REF
    alt: str = Field(pattern=r"^[ACGT]+$") # variant.ALT
    depth: int = Field(ge=0) # variant.INFO["DP"]
    ref_reads: int = Field(ge=0) # variant.INFO["RO"]
    alt_reads: int = Field(ge=0) # variant.INFO["AO"]
    maf: float = Field(ge=0.0, le=1.0) # min(variant.INFO["AF"], 1 - variant.INFO["AF"])
    type: Literal["snp", "ins", "del", "complex", "mnp"] # variant.INFO["TYPE"]

    @model_validator(mode="after")
    def validate_alt_ref_equality(self):
        """Validation function to ensure ALT allele is not equal to REF allele"""
        if self.alt == self.ref:
            raise ValueError("ALT allele cannot equal REF allele")

        return self

    @model_validator(mode="after")
    def validate_read_depths(self):
        """Ensure ref_reads + alt_reads does not exceed depth"""
        if self.ref_reads + self.alt_reads > self.depth:
            raise ValueError(
                f"ref_reads ({self.ref_reads}) + alt_reads ({self.alt_reads}) = "
                f"{self.ref_reads + self.alt_reads} exceeds depth ({self.depth})"
            )

        return self


class AnnotatedVariant(Variant):
    """
    A fully annotated variant produced from Variant and VEP annotations
    Contains all fields from Variant

    Attributes:
        all fields from Variant
        alt_perc (float): Percentage of reads supporting the alternate allele (0.0 to 100.0)
        gene (str): Gene affected by the variant
        consequence (str): Consequence of the variant
    """

    alt_perc: float = Field(ge=0.0, le=100.0) # (alt_reads / (alt_reads + ref_reads)) * 100
    gene: str | None = None # Obtained from VEP API
    consequence: str | None = None # Obtained from VEP API
