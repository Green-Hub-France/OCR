"""
Module d'OCR avec Tesseract: fonctions pour lancer l'OCR rapide et trouver le meilleur zoom.
"""
import logging
from typing import Tuple, List, Optional
from PIL import Image
import pytesseract
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import os

logger = logging.getLogger(__name__)


def ocr_tess(
    img: Image.Image,
    lang: str,
    psm: int,
    conf_thr: int
) -> pd.DataFrame:
    """
Effectue un OCR avec Tesseract sur une image prétraitée.

Args:
    img (Image.Image): Image PIL en niveaux de gris ou binaire.
    lang (str): Langues pour Tesseract (ex: 'fra+eng').
    psm (int): Page segmentation mode pour Tesseract.
    conf_thr (int): Seuil minimal de confiance (0-100) pour filtrer les résultats.

Returns:
    pd.DataFrame: DataFrame contenant colonnes [x1, y1, x2, y2, text, conf].

Raises:
    ValueError: Si `img` n'est pas une image PIL valide ou si `conf_thr` non valide.
    RuntimeError: En cas d'erreur durant l'appel à Tesseract.
"""
    # Validation d'entrée
    if not isinstance(img, Image.Image):
        raise ValueError("Le paramètre 'img' doit être une instance de PIL.Image.Image.")
    if not (0 <= conf_thr <= 100):
        raise ValueError("Le paramètre 'conf_thr' doit être compris entre 0 et 100.")

    try:
        cfg = f"--oem 1 --psm {psm}"
        df = pytesseract.image_to_data(
            img,
            lang=lang,
            config=cfg,
            output_type=pytesseract.Output.DATAFRAME
        )
    except Exception as exc:
        logger.exception("Erreur pendant l'appel à pytesseract.image_to_data")
        raise RuntimeError("Échec de l'OCR Tesseract") from exc

    # Nettoyage des résultats
    df = df.dropna(subset=["text"]).copy()
    # Confiances converties en int
    df["conf"] = df["conf"].astype(int)
    # Filtrer par seuil de confiance
    df = df[df["conf"] >= conf_thr]
    # Renommer et calculer coins
    df = df.rename(columns={"left": "x1", "top": "y1", "width": "w", "height": "h"})
    df["x2"] = df["x1"] + df["w"]
    df["y2"] = df["y1"] + df["h"]
    return df[["x1", "y1", "x2", "y2", "text", "conf"]]


def test_zoom(
    base_img: Image.Image,
    zoom_factor: float,
    preprocess_fn,
    ocr_fn,
    lang: str,
    psm: int,
    conf_thr: int
) -> Tuple[float, int, float, float, pd.DataFrame, Image.Image]:
    """
Test un facteur de zoom pour l'OCR: calibre le nombre de mots détectés et confiance moyenne.

Args:
    base_img (Image.Image): Image de base.
    zoom_factor (float): Facteur de mise à l'échelle.
    preprocess_fn (callable): Fonction de prétraitement d'image.
    ocr_fn (callable): Fonction d'OCR retournant un DataFrame.
    lang (str), psm (int), conf_thr (int): Paramètres d'OCR.

Returns:
    Tuple[zoom, count, mean_conf, score, df, proc_img]
"""
    # Redimensionnement
    w, h = base_img.size
    img = base_img.resize((int(w * zoom_factor), int(h * zoom_factor)), Image.LANCZOS)
    proc_img = preprocess_fn(img)
    df = ocr_fn(proc_img, lang, psm, conf_thr)
    count = len(df)
    mean_conf = float(df["conf"].mean()) if count > 0 else 0.0
    score = count * mean_conf
    return zoom_factor, count, mean_conf, score, df, proc_img


def find_best_zoom(
    base_img: Image.Image,
    lang: str,
    psm: int,
    conf_thr: int,
    preprocess_fn,
    ocr_fn,
    zoom_steps: Optional[List[float]] = None
) -> Tuple[float, int, float, pd.DataFrame, Image.Image, pd.DataFrame]:
    """
Recherche le meilleur facteur de zoom pour maximiser score = count * mean_conf.

Args:
    base_img, lang, psm, conf_thr as above.
    preprocess_fn, ocr_fn: fonctions à utiliser.
    zoom_steps: liste de floats à tester (par défaut [1.0,2.0,3.0,4.0]).

Returns:
    best_zoom (float), count (int), mean_conf (float),
    best_df (pd.DataFrame), best_proc_img (Image.Image), summary (pd.DataFrame)

Raises:
    RuntimeError: Si une erreur se produit pendant le calcul en parallèle.
"""
    if zoom_steps is None:
        zoom_steps = [1.0, 2.0, 3.0, 4.0]

    max_workers = min(32, (os.cpu_count() or 1) + 4)
    results = []
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(test_zoom, base_img, z, preprocess_fn, ocr_fn, lang, psm, conf_thr) for z in zoom_steps]
            for future in futures:
                results.append(future.result())
    except Exception as exc:
        logger.exception("Erreur durant le traitement concurrent de zoom.")
        raise RuntimeError("Échec du calcul du meilleur zoom") from exc

    # Raffinement autour du meilleur
    best_initial = max(results, key=lambda x: x[3])[0]
    neighbors = {best_initial}
    if best_initial - 0.5 >= min(zoom_steps): neighbors.add(best_initial - 0.5)
    if best_initial + 0.5 <= max(zoom_steps): neighbors.add(best_initial + 0.5)

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(test_zoom, base_img, z, preprocess_fn, ocr_fn, lang, psm, conf_thr) for z in neighbors]
            for future in futures:
                results.append(future.result())
    except Exception as exc:
        logger.exception("Erreur durant le raffinage du zoom.")
        # on continue avec les résultats initiaux

    # Choix final
    best = max(results, key=lambda x: x[3])
    best_zoom, count, mean_conf, _, best_df, best_proc_img = best
    # Résumé
    summary = pd.DataFrame([
        {"zoom": zf, "count": cnt, "mean_conf": mc, "score": sc}
        for (zf, cnt, mc, sc, _, _) in results
    ])

    return best_zoom, count, mean_conf, best_df, best_proc_img, summary