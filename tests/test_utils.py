import pytest
from src.utils import extract_entities_ocr

def test_extract_entities_full():
    text = "Facture F1234-56789 le 12/05/2025 montant 1 234,56 €"
    ent = extract_entities_ocr(text)
    assert ent['invoice_number'] == 'F1234-56789'
    assert '12/05/2025' in ent['dates']
    assert '1 234,56 €' in ent['amounts']
