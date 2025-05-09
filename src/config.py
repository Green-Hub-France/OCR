# src/config.py
# ----------------
"""
Configuration management for OCR - Green Hub application.
Loads environment variables, supports AWS Secrets Manager integration,
and provides constants and helper functions for application configuration.
"""
import os
import json
from typing import Optional, Dict
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Paths and AWS configuration
TESSDATA_PREFIX: Optional[str] = os.getenv('TESSDATA_PREFIX')
AWS_ACCESS_KEY_ID: Optional[str] = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION: str = os.getenv('AWS_REGION', 'eu-west-3')
# Optional AWS Secrets Manager secret name
SECRET_NAME: Optional[str] = os.getenv('AWS_SECRETS_NAME')

# Streamlit page configuration
STREAMLIT_PAGE_TITLE: str = os.getenv('STREAMLIT_PAGE_TITLE', 'OCR - Green Hub')
STREAMLIT_LAYOUT: str = os.getenv('STREAMLIT_LAYOUT', 'wide')

# Load AWS credentials from Secrets Manager if configured
if SECRET_NAME:
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        client = boto3.client('secretsmanager', region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=SECRET_NAME)
        secret_str = resp.get('SecretString', '{}')
        secrets: Dict[str, str] = json.loads(secret_str)
        AWS_ACCESS_KEY_ID = secrets.get('AWS_ACCESS_KEY_ID') or AWS_ACCESS_KEY_ID
        AWS_SECRET_ACCESS_KEY = secrets.get('AWS_SECRET_ACCESS_KEY') or AWS_SECRET_ACCESS_KEY
    except (ClientError, BotoCoreError, ImportError, json.JSONDecodeError) as e:
        # If secret retrieval fails, fall back to environment variables
        from logging import getLogger

        logger = getLogger(__name__)
        logger.error(f"Unable to load AWS secrets from Secrets Manager: {e}")


def validate_aws_credentials() -> bool:
    """
    Check whether AWS credentials are set (either via env vars or Secrets Manager).

    Returns:
        bool: True if both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are available.
    """
    return bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)


def get_textract_client_params() -> Dict[str, str]:
    """
    Build parameters for boto3 Textract client instantiation.

    Returns:
        Dict[str, str]: Mapping of boto3 client args.
    """
    params: Dict[str, str] = {'region_name': AWS_REGION}
    if validate_aws_credentials():
        params.update({
            'aws_access_key_id': AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
        })
    return params