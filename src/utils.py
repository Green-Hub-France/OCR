import re
from flashtext import KeywordProcessor
from typing import Dict, List, Optional

date_pattern = r"(?:\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})"
amount_pattern = r"\b\d{1,3}(?:[ \u00A0]\d{3})*(?:[.,]\d{2})?\s?€\b"

keyword_processor = KeywordProcessor()
keyword_processor.add_keyword('invoice', 'INVOICE_NUMBER')

def extract_entities_ocr(text: str) -> Dict[str, Optional[List[str]]]:
    entities: Dict[str, Optional[List[str]]] = {}
    m = re.search(r"[Ff]\d{4}-\d{5}", text)
    entities['invoice_number'] = m.group(0) if m else None
    entities['dates'] = re.findall(date_pattern, text)
    entities['amounts'] = re.findall(amount_pattern, text)
    return entities
