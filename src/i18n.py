# src/i18n.py
# --------------

from typing import Literal

# Dictionnaire de traductions
_TRANSLATIONS = {
    "fr": {
        "config_header": "Configuration OCR",
        "lang_label": "Langues Tesseract",
        "lang_help": "Liste des codes de langue pour Tesseract, ex: 'fra+eng'",
        "conf_label": "Seuil confiance (Textract & OCR)",
        "conf_help": "Filtre les résultats en-dessous de ce pourcentage de confiance",
        "psm_label": "PSM Tesseract",
        "psm_help": "Mode de segmentation de page Tesseract (ex: 3 = Fully automatic)",
        "auto_zoom_label": "Auto-Zoom Tesseract",
        "auto_zoom_help": "Permet d'essayer plusieurs niveaux de zoom pour optimiser l'OCR",
        "validate": "Valider",
        "tab_single": "Test unique",
        "tab_batch": "Batch Textract",
        "analyze_tex": "Analyser via Textract",
        "go_ocr": "GO Tesseract OCR",
        "single_uploader": "Image ou PDF (single)",
        "single_uploader_help": "Charger un seul fichier image ou PDF pour test",
        "batch_uploader": "Ajouter plusieurs fichiers",
        "batch_uploader_help": "Charger plusieurs fichiers pour traitement en lot",
        "pdf_page": "Page PDF",
        "pdf_page_help": "Numéro de la page à extraire du PDF (1-index)",
        "res_tex": "Champs détectés (Textract)",
        "zoom_summary": "Zoom & Résumé",
        "ocr_results": "Résultats OCR",
        "ocr_spinner": "Traitement OCR en cours...",
        "mean_conf_msg": "Confiance moyenne",
        "lines_msg": "Nombre de lignes détectées",
        "batch_summary": "Résumé Batch Textract",
        "details": "Détails des résultats par fichier",
        "no_fields": "Aucun champ détecté pour ce fichier."
    },
    "en": {
        "config_header": "OCR Configuration",
        "lang_label": "Tesseract Languages",
        "lang_help": "Comma-separated Tesseract language codes, e.g. 'fra+eng'",
        "conf_label": "Confidence Threshold (Textract & OCR)",
        "conf_help": "Filter out results below this confidence percentage",
        "psm_label": "Tesseract PSM",
        "psm_help": "Page segmentation mode for Tesseract (e.g. 3 = Fully automatic)",
        "auto_zoom_label": "Auto-Zoom Tesseract",
        "auto_zoom_help": "Automatically try multiple zoom levels to optimize OCR",
        "validate": "Apply",
        "tab_single": "Single Test",
        "tab_batch": "Batch Textract",
        "analyze_tex": "Analyze with Textract",
        "go_ocr": "Run Tesseract OCR",
        "single_uploader": "Image or PDF (single)",
        "single_uploader_help": "Upload a single image or PDF file for testing",
        "batch_uploader": "Add multiple files",
        "batch_uploader_help": "Upload multiple files for batch processing",
        "pdf_page": "PDF Page",
        "pdf_page_help": "Page number to extract from the PDF (1-indexed)",
        "res_tex": "Detected Fields (Textract)",
        "zoom_summary": "Zoom & Summary",
        "ocr_results": "OCR Results",
        "ocr_spinner": "OCR processing...",
        "mean_conf_msg": "Average confidence",
        "lines_msg": "Number of lines detected",
        "batch_summary": "Batch Textract Summary",
        "details": "Details per file",
        "no_fields": "No fields detected for this file."
    }
}

def t(key: str, lang: Literal["fr", "en"] = "fr") -> str:
    """
    Retourne la traduction pour la clé donnée et la langue choisie.
    """
    return _TRANSLATIONS.get(lang, {}).get(key, key)