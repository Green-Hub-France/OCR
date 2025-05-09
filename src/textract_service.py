import boto3
from typing import List, Dict, Any
import logging
from .config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

logger = logging.getLogger(__name__)

client_args: Dict[str, Any] = {'region_name': AWS_REGION}
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    client_args.update({
        'aws_access_key_id': AWS_ACCESS_KEY_ID,
        'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
    })

textract_client = boto3.client('textract', **client_args)

def parse_textract_kv(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocks = resp.get('Blocks', [])
    block_map = {b['Id']: b for b in blocks}
    kv_list: List[Dict[str, Any]] = []

    for b in blocks:
        if b['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in b.get('EntityTypes', []):
            key_text = ''
            key_confs: List[float] = []
            value_text = ''
            value_confs: List[float] = []
            for rel in b.get('Relationships', []):
                if rel['Type'] == 'CHILD':
                    for cid in rel['Ids']:
                        word = block_map[cid]
                        if word['BlockType'] == 'WORD':
                            key_text += word.get('Text', '') + ' '
                            key_confs.append(word.get('Confidence', 0.0))
            for rel in b.get('Relationships', []):
                if rel['Type'] == 'VALUE':
                    for vid in rel['Ids']:
                        vb = block_map[vid]
                        for vrel in vb.get('Relationships', []):
                            if vrel['Type'] == 'CHILD':
                                for cid2 in vrel['Ids']:
                                    word = block_map[cid2]
                                    if word['BlockType'] == 'WORD':
                                        value_text += word.get('Text', '') + ' '
                                        value_confs.append(word.get('Confidence', 0.0))
            key_text = key_text.strip()
            value_text = value_text.strip()
            avg_conf = round(sum(value_confs) / len(value_confs), 1) if value_confs else 0.0
            if key_text:
                kv_list.append({'key': key_text, 'value': value_text, 'conf': avg_conf})
    return kv_list
def textract_parse(img_bytes: bytes) -> List[Dict[str, Any]]:
    try:
        resp = textract_client.analyze_document(
            Document={'Bytes': img_bytes},
            FeatureTypes=['FORMS']
        )
        return parse_textract_kv(resp)
    except Exception:
        logger.exception('Textract error')
        return []
