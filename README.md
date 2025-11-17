# Tempus Bioinformatics Technical Challenge

This project creates a variant annotation tool that accepts an input vcf and outputs an annotated csv

## Setup

Use [Poetry](https://python-poetry.org/docs/#installation) or pip:
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
Default for `--vcf` is the `challenge_data.vcf`, also found in the [repo](./challenge_data.vcf). The other arguments also have defaults that can be seen in [PyDocs](./PyDocs.md)

## Source Code Overview

Refer to [PyDocs](./PyDocs.md) for function signatures and more information on attributes and classes.

#### [variant_annotation](variant_annotation.py)

Driver script that orchestrates the entire process from parsing input to writing annotations of variants in an output file. Creates batches of variants where each batch of variants is processed by a thread. Batches of variants helps in making efficient POST requests to the VEP API. After computing the annotations of each variant, all of the annotation info is written to a csv in the order in which they were present in the VCF file.

#### [annotation](src/annotation.py)

Module with functions to iterate over a VCF and annotate them. Creates an instance of the Variant model for each ALT allele of a variant. Once the Variant model is populated, the VEP API is queried using a computed string made from the chromosome, reference allele, alternate allele and start position. Batch requests are made to the VEP API for efficiency. The information obtained from the VEP API, plus the original information in the Variant model are put together to create the AnnotatedVariant model.

#### [config](src/config.py)

Helper file with constants

#### [models](src/models.py)

Module with definitions of Pydantic models for Variant and AnnotatedVariant. Also contains some basic validation around fields of the models.

#### [vep](src/vep.py)

Module with helper functions to interact with Ensembl VEP REST API and parse data retrieved from the API

## Output Overview 

Output file can be found at [annotated_variants.csv](./annotated_variants.csv)

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
| type | Type of variant (snp, ins, del, complex, mnp) |
| alt_perc | Percentage of reads supporting alternate allele |
| gene | Gene id affected by the variant |
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
 - **type**: one value in variant.INFO["TYPE"] if it's comma separated, else just variant.INFO["TYPE"]
 - **alt_perc**: alt_reads / (alt_reads + ref_reads) * 100
 - **gene**: get gene_id of transcript where "consequence_terms" matches "most_severe_consequence"
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
 - Also using gene_id instead of gene_symbol for the annotation
 - Not reporting all consequences of all transcripts
 - Inferring type from TYPE attribute of INFO field of VCF

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

 - Set more default values for fields that are read in from VCF. The example VCF is clean and has all values for all fields, but in some cases there might be fields with values missing and that would cause this tool to error out
 - No testing at all. Should test all computations and querying of the API. Ideally set up unit tests using pytest
 - All threads wait for the computation of all threads to finish, and then they are given work again. This waiting is unnecessary. Threads should be released the moment their result is consumed.
 - Optimal number of threads and optimal batch size can be obtained using more benchmarking
 - More comprehensive variant typing by looking at REF and ALT allele sequences
 - More validation on both data in vcf and data obtained from VEP API
 - Setup github action that automatically generates [PyDocs.md](./PyDocs.md) whenever there is a change in source code
 - Add `summary` mode to script that parses the vcf file and prints some summary statistics
 - Enforce line length for py scripts
 - More info from both VEP API and VCF could be added to annotated csv based on requirements