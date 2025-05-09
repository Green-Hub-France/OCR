import pytest
from src.textract_service import parse_textract_kv

def fake_blocks_response():
    # Simulate minimal Textract response with one key-value
    blocks = [
        {
            'Id': '1', 'BlockType': 'KEY_VALUE_SET', 'EntityTypes': ['KEY'],
            'Relationships': [{'Type':'CHILD','Ids':['2']}, {'Type':'VALUE','Ids':['3']}]
        },
        {'Id':'2','BlockType':'WORD','Text':'Invoice'},
        {
            'Id':'3','BlockType':'KEY_VALUE_SET','Relationships':[{'Type':'CHILD','Ids':['4']}]
        },
        {'Id':'4','BlockType':'WORD','Text':'12345'}
    ]
    return {'Blocks': blocks}

def test_parse_textract_kv():
    resp = fake_blocks_response()
    kvs = parse_textract_kv(resp)
    assert isinstance(kvs, list)
    assert kvs and kvs[0]['key'] == 'Invoice'
    assert kvs[0]['value'] == '12345'
    assert 'conf' in kvs[0]
