"""
Author: Utsab Ray

Created: 2025-11-17

Description:
    Helper functions to interact with Ensembl VEP REST API and parse data retrieved from the API
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)
import requests
from src.config import VEP_GRCH37_URL, VEP_HEADERS


def get_genes_for_most_severe_consequence(vep_record: dict) -> str | None:
    """
    Get gene for transcript matching most severe consequence

    Args:
        vep_record (dict): Single VEP JSON record for a variant

    Returns:
        String of gene symbol where "consequence_terms" matches "most_severe_consequence"
        Or None if "transcript_consequences" key is not present in @vep_record
    """
    most_severe = vep_record["most_severe_consequence"]
    for transcript in vep_record.get("transcript_consequences", []):
        cons_terms = transcript["consequence_terms"]
        if most_severe in cons_terms:
            return transcript["gene_symbol"]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
    | retry_if_exception_type(requests.exceptions.HTTPError)
    | retry_if_exception_type(requests.exceptions.ConnectionError)
    | retry_if_exception_type(requests.exceptions.JSONDecodeError),
    reraise=False,
)
def make_vep_request(payload: dict) -> dict:
    """
    Calls the VEP REST API and retrieves annotation data for a batch of variants
    Implement retries using tenacity. Retry strategy is exponential backoff with a max wait time of 60 seconds. After 3 failed attempts, give up and return None
    https://github.com/jd/tenacity?tab=readme-ov-file#waiting-before-retrying

    Args:
        payload (dict): Payload to send to the VEP REST API. Contains batch of HGVS notations to be annotated

    Returns:
        JSON response from the VEP REST API
    """
    response = requests.post(
        VEP_GRCH37_URL, json=payload, headers=VEP_HEADERS, timeout=10
    )
    response.raise_for_status()
    return response.json()
