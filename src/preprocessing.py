"""
Module de prétraitement des images pour l'application OCR - Green Hub.
Inclut la conversion en niveaux de gris, CLAHE, seuillage adaptatif et fermeture morphologique.
"""
import streamlit as st
import logging
from typing import Tuple
from PIL import Image
import numpy as np
import cv2

logger = logging.getLogger(__name__)

@st.cache_data(show_spinner=False)
def preprocess(
    img: Image.Image,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
    thresh_block_size: int = 15,
    thresh_C: int = 3,
    morph_kernel: Tuple[int, int] = (3, 3)
) -> Image.Image:
    """
    Améliore la lisibilité d'une image pour l'OCR en appliquant :
    1. Conversion en niveaux de gris
    2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    3. Seuillage adaptatif gaussien
    4. Fermeture morphologique

    Args:
        img (Image.Image): Image PIL en couleur.
        clip_limit (float): Limite de contraste pour CLAHE.
        tile_grid_size (Tuple[int, int]): Taille de la grille pour CLAHE.
        thresh_block_size (int): Taille du bloc (impair) pour le seuillage adaptatif.
        thresh_C (int): Constante soustraite dans le seuillage adaptatif.
        morph_kernel (Tuple[int, int]): Taille du noyau pour la fermeture morphologique.

    Returns:
        Image.Image: Image binaire traitée prête pour l'OCR.

    Raises:
        ValueError: Si `img` n'est pas une instance de PIL.Image.Image.
        RuntimeError: En cas d'erreur lors du traitement OpenCV.
    """
    # Validation d'entrée
    if not isinstance(img, Image.Image):
        raise ValueError("L'argument 'img' doit être une instance de PIL.Image.Image.")

    try:
        # Conversion en niveaux de gris
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        # CLAHE
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        cl = clahe.apply(gray)
        # Seuillage adaptatif
        th = cv2.adaptiveThreshold(
            cl,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=thresh_block_size,
            C=thresh_C
        )
        # Fermeture morphologique
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, morph_kernel)
        closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)
        return Image.fromarray(closed)
    except Exception as exc:
        logger.exception("Erreur lors du prétraitement de l'image")
        raise RuntimeError("Échec du prétraitement de l'image") from exc
