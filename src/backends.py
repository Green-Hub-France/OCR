# src/backends.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from PIL import Image

class OCRBackend(ABC):
    @abstractmethod
    def recognize(self, *args, **kwargs) -> Any:
        pass

class TesseractBackend(OCRBackend):
    def recognize(self, image: Image.Image, lang='eng', psm=6, conf_thr=30) -> Dict:
        # Implement Tesseract OCR logic
        return {}

class TextractBackend(OCRBackend):
    def recognize(self, image_bytes: bytes) -> Dict:
        # Implement AWS Textract OCR logic
        return {}

class GoogleVisionBackend(OCRBackend):
    def recognize(self, image_bytes: bytes) -> Dict:
        # Implement Google Vision API call
        return {}

class AzureVisionBackend(OCRBackend):
    def recognize(self, image_bytes: bytes) -> Dict:
        # Implement Azure Computer Vision API call
        return {}
