"""
Author: Utsab Ray

Created: 2025-11-17

Description:
    Config file with constants for VEP API
    For production code, provide way to override these via command line or environment variables
"""

VEP_GRCH37_URL = "https://grch37.rest.ensembl.org/vep/human/hgvs"
VEP_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
