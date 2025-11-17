"""
Author: Utsab Ray

Created: 2025-11-17

Description:
    Driver script to annotate every variant in a VCF file and output results to a CSV

Usage:
    python variant_annotation.py

Args:
    --vcf: Path to input VCF file (default: challenge_data.vcf)
    --output: Path to output CSV file with annotated variants (default: annotated_variants.csv)
    --threads: Number of threads for parallel processing (default: 8, max: 32)
    --batch_size: Number of variants to process in each batch, relevant for querying Ensembl VEP API (default: 100)

Note:
    Writes CSV file with annotated variants
"""

import argparse
from pathlib import Path
import csv
from concurrent.futures import ThreadPoolExecutor, Future
from src.annotation import read_vcf, build_annotation
from src.models import AnnotatedVariant


def main():
    """
    Driver function to accept command line arguments, iterate through VCF variants in batches using multiple threads and write the results to a CSV
    """
    parser = argparse.ArgumentParser(description="Annotate each variant in a VCF file")
    parser.add_argument(
        "--vcf", type=Path, default="challenge_data.vcf", help="Path to input VCF file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="annotated_variants.csv",
        help="Path to output CSV file with annotated variants",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=8,
        help="Number of threads for parallel processing (max 32)",
        choices=range(1, 33),
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=100,
        help="Number of variants to process in each batch",
    )

    args = parser.parse_args()

    with open(args.output, "w") as csvfile:
        # Get field names from the model so we can write the header before getting an instance of the model
        fieldnames = list(AnnotatedVariant.model_fields.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Create thread pool once and reuse for all batches
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            # Batch of variants with max length of list equal to args.batch_size
            batch = []
            # Each future represents an object to be called, where an individual thread is responsible for the called object and all of its computation
            futures = []

            for variant in read_vcf(args.vcf):
                batch.append(variant)

                # When args.batch_size variants stored in batch, send batch for processing
                if len(batch) == args.batch_size:
                    # Submit batch to a single thread for processing
                    future = executor.submit(build_annotation, batch)
                    # Order in which @future is inserted is order in which results are retrieved and written
                    futures.append(future)

                    # Reset batch for future variants
                    batch = []

                    # When we have created args.threads number of threads, wait for all threads to finish, write results, and then resume processing
                    if len(futures) == args.threads:
                        write_futures_in_order(futures, writer)
                        futures = []

            # Variants left at the end where the main for loop exited, but there were still unprocessed variants in @batch
            if batch:
                future = executor.submit(build_annotation, batch)
                futures.append(future)

            # This cannot be a part of the if condition above, since there might be unprocessed futures, even if @batch is empty
            if futures:
                write_futures_in_order(futures, writer)


def write_futures_in_order(futures: list[Future], writer: csv.DictWriter):
    """
    Wait for futures to complete and write results to @writer in submission order. This is a blocking function

    Args:
        futures (list[Future]): Single unit of work which is responsible for a batch of variants
        writer (csv.DictWriter): Enable writing of AnnotatedVariant model instances to a csv

    Note:
        Write all annotated variants processed by all threads in @futues
    """
    for future in futures:
        # Blocks until this specific future completes
        annotated_variant_batch = future.result()
        for annotated_variant in annotated_variant_batch:
            writer.writerow(annotated_variant.model_dump())


if __name__ == "__main__":
    main()
