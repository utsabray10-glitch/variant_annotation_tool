<a id="variant_annotation"></a>

# variant\_annotation

Author: Utsab Ray

Created: 2025-11-17

Description:
Driver script to annotate every variant in a VCF file and output results to a CSV

Usage:
python variant_annotation.py

**Arguments**:

- `--vcf` - Path to input VCF file (default: challenge_data.vcf)
- `--output` - Path to output CSV file with annotated variants (default: annotated_variants.csv)
- `--threads` - Number of threads for parallel processing (default: 8, max: 32)
- `--batch_size` - Number of variants to process in each batch, relevant for querying Ensembl VEP API (default: 100)
  

**Notes**:

  Writes CSV file with annotated variants

<a id="variant_annotation.main"></a>

#### main

```python
def main()
```

Entrypoint to accept command line arguments

<a id="variant_annotation.process"></a>

#### process

```python
def process(output: Path, vcf: Path, threads: int, batch_size: int)
```

Driver function to iterate through VCF variants in batches using multiple threads and write the results to a CSV

**Arguments**:

- `output` _Path_ - Path to output CSV file with annotated variants
- `vcf` _Path_ - Path to input VCF file
- `threads` _int_ - Number of threads for parallel processing
- `batch_size` _int_ - Number of variants to process in each batch

<a id="variant_annotation.write_futures_in_order"></a>

#### write\_futures\_in\_order

```python
def write_futures_in_order(futures: list[Future], writer: csv.DictWriter)
```

Wait for futures to complete and write results to @writer in submission order. This is a blocking function

**Arguments**:

- `futures` _list[Future]_ - Single unit of work which is responsible for a batch of variants
- `writer` _csv.DictWriter_ - Enable writing of AnnotatedVariant model instances to a csv
  

**Notes**:

  Write all annotated variants processed by all threads in @futues

<a id="src.models"></a>

# src.models

Author: Utsab Ray

Created: 2025-11-17

Description:
    Module with definitions of Pydantic models for Variant and AnnotatedVariant

<a id="src.models.Variant"></a>

## Variant

```python
class Variant(BaseModel)
```

A variant record from a VCF file

**Attributes**:

- `chrom` _str_ - Chromosome ID
- `pos` _int_ - 1-based position of the variant
- `ref` _str_ - Reference allele sequence
- `alt` _str_ - Alternate allele sequence
- `depth` _int_ - Read depth at the variant position
- `ref_reads` _int_ - Number of reads supporting the reference allele
- `alt_reads` _int_ - Number of reads supporting the alternate allele
- `maf` _float_ - Minor allele frequency (0 to 1)
- `type` _str_ - Type of variant ("snp", "ins", "del", "complex", "mnp")

<a id="src.models.Variant.pos"></a>

#### pos

variant.POS

<a id="src.models.Variant.ref"></a>

#### ref

variant.REF

<a id="src.models.Variant.alt"></a>

#### alt

variant.ALT

<a id="src.models.Variant.depth"></a>

#### depth

variant.INFO["DP"]

<a id="src.models.Variant.ref_reads"></a>

#### ref\_reads

variant.INFO["RO"]

<a id="src.models.Variant.alt_reads"></a>

#### alt\_reads

variant.INFO["AO"]

<a id="src.models.Variant.maf"></a>

#### maf

min(variant.INFO["AF"], 1 - variant.INFO["AF"])

<a id="src.models.Variant.type"></a>

#### type

variant.INFO["TYPE"]

<a id="src.models.Variant.validate_alt_ref_equality"></a>

#### validate\_alt\_ref\_equality

```python
@model_validator(mode="after")
def validate_alt_ref_equality()
```

Validation function to ensure ALT allele is not equal to REF allele

<a id="src.models.Variant.validate_read_depths"></a>

#### validate\_read\_depths

```python
@model_validator(mode="after")
def validate_read_depths()
```

Ensure ref_reads + alt_reads does not exceed depth

<a id="src.models.AnnotatedVariant"></a>

## AnnotatedVariant

```python
class AnnotatedVariant(Variant)
```

A fully annotated variant produced from Variant and VEP annotations
Contains all fields from Variant

**Attributes**:

  all fields from Variant
- `alt_perc` _float_ - Percentage of reads supporting the alternate allele (0.0 to 100.0)
- `gene` _str_ - Gene affected by the variant
- `consequence` _str_ - Consequence of the variant

<a id="src.models.AnnotatedVariant.alt_perc"></a>

#### alt\_perc

(alt_reads / (alt_reads + ref_reads)) * 100

<a id="src.models.AnnotatedVariant.gene"></a>

#### gene

Obtained from VEP API

<a id="src.models.AnnotatedVariant.consequence"></a>

#### consequence

Obtained from VEP API

<a id="src.annotation"></a>

# src.annotation

Author: Utsab Ray

Created: 2025-11-17

Description:
    Module with functions to iterate over a vcf and annotate them

<a id="src.annotation.read_vcf"></a>

#### read\_vcf

```python
def read_vcf(input_vcf: Path) -> Generator[Variant, None, None]
```

Iterate through VCF and yield instance(s) of Variant for each variant

**Arguments**:

- `input_vcf` _Path_ - Path to the input VCF file
  

**Returns**:

  Yield one instance of Variant

<a id="src.annotation.build_annotation"></a>

#### build\_annotation

```python
def build_annotation(
        variant_data_batch: list[Variant]) -> list[AnnotatedVariant]
```

Annotate each individual variant with info from VEP API and some additional stats

**Arguments**:

- `variant_data_batch` _list[Variant]_ - All instances of Variant that are to be annotated
  

**Returns**:

  List of instances of AnnotatedVariant that represents all info related to annotated variants

<a id="src.annotation.ensure_tuple"></a>

#### ensure\_tuple

```python
def ensure_tuple(value: tuple | int) -> tuple
```

Convert single values to tuple for consistent iteration downstream

**Arguments**:

- `value` _tuple|int_ - Convert to tuple if int to ensure downstream processing has consistent syntax
  

**Returns**:

  Tuple

<a id="src.vep"></a>

# src.vep

Author: Utsab Ray

Created: 2025-11-17

Description:
    Helper functions to interact with Ensembl VEP REST API and parse data retrieved from the API

<a id="src.vep.get_genes_for_most_severe_consequence"></a>

#### get\_genes\_for\_most\_severe\_consequence

```python
def get_genes_for_most_severe_consequence(vep_record: dict) -> str | None
```

Get gene for transcript matching most severe consequence

**Arguments**:

- `vep_record` _dict_ - Single VEP JSON record for a variant
  

**Returns**:

  String of gene symbol where "consequence_terms" matches "most_severe_consequence"
  Or None if "transcript_consequences" key is not present in @vep_record

<a id="src.vep.make_vep_request"></a>

#### make\_vep\_request

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
    | retry_if_exception_type(requests.exceptions.HTTPError)
    | retry_if_exception_type(requests.exceptions.ConnectionError)
    | retry_if_exception_type(requests.exceptions.JSONDecodeError),
    reraise=False,
)
def make_vep_request(payload: dict) -> dict
```

Calls the VEP REST API and retrieves annotation data for a batch of variants
Implement retries using tenacity. Retry strategy is exponential backoff with a max wait time of 60 seconds. After 3 failed attempts, give up and return None
https://github.com/jd/tenacity?tab=readme-ov-file#waiting-before-retrying

**Arguments**:

- `payload` _dict_ - Payload to send to the VEP REST API. Contains batch of variants to be annotated
  

**Returns**:

  JSON response from the VEP REST API

<a id="src.config"></a>

# src.config

Author: Utsab Ray

Created: 2025-11-17

Description:
    Config file with constants for VEP API
    For production code, provide way to override these via command line or environment variables

