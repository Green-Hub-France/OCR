# src/secrets.py
# --------------------
"""
Module pour récupérer des secrets depuis AWS Secrets Manager.
"""
import os
import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

def get_aws_secret(secret_name: str, region_name: str) -> dict:
    """
    Récupère et retourne le contenu JSON du secret `secret_name`.
    """
    client = boto3.client('secretsmanager', region_name=region_name)
    try:
        resp = client.get_secret_value(SecretId=secret_name)
        secret_str = resp.get('SecretString', '{}')
        return json.loads(secret_str)
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Impossible de récupérer le secret {secret_name}: {e}")
        return {}
