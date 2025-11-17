"""
Author: Utsab Ray

Created: 2025-11-17

Description:
    Module with function to compute HGVS genomic notation from variant info
"""
def make_hgvs(chrom: str, pos: int, ref: str, alt: str) -> tuple[str, str]:
    """
    Convert a VCF variant (CHROM, POS, REF, ALT) into HGVS genomic notation.
    Handles:
      - SNPs
      - Insertions
      - Deletions
      - Deletion-insertion (delins)
    
    Args:
        chrom (str): Chromosome (e.g., "1", "X", "MT
        pos (int): 1-based position of the variant
        ref (str): Reference allele sequence
        alt (str): Alternate allele sequence
    
    Returns:
        Tuple of (hgvs_notation (str), variant_type (str)) where variant_type is one of:
            - "sub" for SNPs
            - "ins" for insertions
            - "del" for deletions
            - "delins" for deletion-insertions
    """

    # trim shared prefix
    prefix = 0
    while prefix < len(ref) and prefix < len(alt) and ref[prefix] == alt[prefix]:
        prefix += 1

    ref_trimmed = ref[prefix:]
    alt_trimmed = alt[prefix:]
    pos = int(pos + prefix)  # update POS to where change actually starts

    # trim shared suffix
    suffix = 0
    while (
        suffix < len(ref_trimmed) and
        suffix < len(alt_trimmed) and
        ref_trimmed[-(suffix + 1)] == alt_trimmed[-(suffix + 1)]
    ):
        suffix += 1

    if suffix > 0:
        ref_final = ref_trimmed[:-suffix]
        alt_final = alt_trimmed[:-suffix]
    else:
        ref_final = ref_trimmed
        alt_final = alt_trimmed

    # SNP
    if len(ref_final) == 1 and len(alt_final) == 1:
        return f"{chrom}:g.{pos}{ref_final}>{alt_final}", "sub"

    # Pure deletion
    if len(ref_final) > 0 and len(alt_final) == 0:
        if len(ref_final) == 1:
            return f"{chrom}:g.{pos}del", "del"
        else:
            end = pos + len(ref_final) - 1
            return f"{chrom}:g.{pos}_{end}del", "del"

    # Pure insertion
    if len(ref_final) == 0 and len(alt_final) > 0:
        # insertion happens *between* pos-1 and pos
        left = pos - 1
        right = pos
        return f"{chrom}:g.{left}_{right}ins{alt_final}", "ins"

    # Delins (complex variant)
    # Deletes ref_final and replaces with alt_final
    end = pos + len(ref_final) - 1
    return f"{chrom}:g.{pos}_{end}delins{alt_final}", "delins"