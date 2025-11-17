# Tempus Bioinformatics Technical Challenge

This project creates a variant annotation tool that accepts an input vcf and outputs an annotated csv

## Setup

Use [Poetry](https://python-poetry.org/) or pip:
```bash
poetry install
eval "$(poetry env activate)"
# or
pip install -r requirements.txt
```
The `eval` will activate the virtual environment that Poetry created
requirements.txt file was generated using:
```bash
poetry export -f requirements.txt --output requirements.txt --with dev --without-hashes
```

## Usage

```bash
python variant_annotation.py --vcf <input vcf> --output <output csv> --threads <num threads for parallel processing> --batch_size <num variants to process together in one thread and one VEP API request>
```
Default for `--vcf` is the `challenge_data.vcf`. The other arguments also have defaults that can be seen in [PyDocs](PyDocs.md)

## Source Code Overview

#### [variant_annotation](variant_annotation.py)

Driver script that orchestrates the entire process from parsing input to writing annotations of variants in an output file. Creates batches of variants where each batch of variants is processed by a thread. Batches of variants helps in making efficient POST requests to the VEP API. After computing the annotations of each variant, all of the annotation info is written to a csv in the order in which they were present in the VCF file.

#### [annotation](src/annotation.py)

Module with functions to iterate over a VCF and annotate them. Creates an instance of the Variant model for each ALT allele of a variant. Once the Variant model is populated, the VEP API is queried using a computed HGVS string. Batch requests are made to the VEP API for efficiency. The information obtained from the VEP API, plus the original information in the Variant model are put together to create the AnnotatedVariant model.

#### [compute_hgvs](src/compute_hgvs.py)

Module with function to compute HGVS genomic notation

#### [config](src/config.py)

Helper file with constants

#### [models](src/models.py)

Module with definitions of Pydantic models for Variant and AnnotatedVariant. Also contains some basic validation around fields of the models.

#### [vep](src/vep.py)

## Output Overview

| Column | Description |
|--------|-------------|
| chrom | Chromosome identifier |
| pos | Genomic position (1-based) |
| ref | Reference allele sequence |
| alt | Alternate allele sequence |
| depth | Total read depth at position |
| ref_reads | Number of reads supporting reference allele |
| alt_reads | Number of reads supporting alternate allele |
| maf | Minor allele frequency (0.0 to 1.0) |
| alt_perc | Percentage of reads supporting alternate allele (0.0 to 100.0) |
| variant_type | Type of variant (SNP, insertion, deletion, delins) |
| gene | Gene symbol affected by the variant |
| consequence | Most severe consequence from VEP annotation |

### Methodology

 - **chrom**: variant.CHROM
 - **pos**: variant.POS
 - **ref**: variant.REF
 - **alt**: one ALT in variant.ALT if it's a list, else just variant.ALT
 - **depth**: variant.INFO["DP"]
 - **ref_reads**: variant.INFO["RO"]
 - **alt_reads**: one value in variant.INFO["AO"] if it's a list, else just variant.INFO["AO"]
 - **maf**: Minimum(variant.INFO["AF"], 1 - variant.INFO["AF"]). variant.INFO["AF"] could also be a list in which case we pick one value
 - **alt_perc**: alt_reads / (alt_reads + ref_reads) * 100
 - **variant_type**: infered from ref and alt, either "sub", "ins", "del" or "delins"
 - **gene**: get gene of transcript where "consequence_terms" matches "most_severe_consequence"
 - **consequence**: most severe consequence

## Documentation

Auto-generated documentation from docstrings using [pydoc-markdown](https://github.com/NiklasRosenstein/pydoc-markdown) can be found at [PyDocs.md](./PyDocs.md):
```bash
pydoc-markdown > PyDocs.md
```
YAML file for configuring pydoc-markdown is [here](./pydoc-markdown.yaml)

## Assumptions

 - Breaking each ALT allele into it's own variant in the output csv
 - Getting gene of transcript where the most severe consequence is one of the consequence terms. Alternative would be to report all genes
 - Not reporting all consequences of all transcripts
 - Computing HGVS notation based on REF and ALT and not on CIGAR string
 - Not reporting multi nucleotide polymorphism(mnp) and complex variants separately, but bundling them up into `delins`

## Parallelism and Batching

Since the VEP API takes a while to respond, the best approach to efficiently query the API is to batch query it. We create n number of worker threads. Each worker thread gets assigned a batch of variants, which it then processes. Batches are assigned to threads one after the other, and once all threads have been assigned batches, we wait for all threads to finish computation. Once computation is finished, the annotated variant information is written in the order in which the entries were present in the vcf file. The order is preserved by keeping track of the order in which threads were assigned batches.

Here is some very preliminary benchmarking done by varying the number of threads. Something similar can be done with batch size as well.

| Threads | Execution Time (seconds) |
|---------|--------------------------|
| 16      | 21.46                    |
| 8       | 37.98                    |
| 4       | 68.41                    |
| 2       | 130.83                   |

## Limitations and Improvements

 - No testing at all. Should test all computations and querying of the API
 - All threads wait while computation of all of them is finished. This waiting is unnecessary. Threads should be released the moment their result is consumed.
 - Optimal number of threads and optimal batch size can be obtained using more benchmarking
 - Support for generating HGVS notation for more variant types
 - More validation on both data in vcf and data obtained from VEP API
