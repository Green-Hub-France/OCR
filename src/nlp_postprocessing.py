# src/nlp_postprocessing.py
import spacy
from typing import Dict

nlp = spacy.load("fr_core_news_sm")

def normalize_entities(entities: Dict) -> Dict:
    # Normalize dates, numbers, apply NLP corrections
    return entities
