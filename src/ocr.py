# src/ocr.py

"""
Module d'OCR avec Tesseract : fonctions pour lancer l'OCR rapide
et trouver le meilleur zoom sans planter en cas d'erreur.
"""

import logging
from typing import Tuple, List, Optional, Callable, Any
from PIL import Image
import pytesseract
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


def ocr_tess(
    img: Image.Image,
    lang: str,
    psm: int,
    conf_thr: int
) -> pd.DataFrame:
    """
    Effectue un OCR Tesseract sur une image prétraitée,
    filtre par confiance et renvoie un DataFrame.

    Args:
        img: Image PIL en niveaux de gris ou binaire.
        lang: Langues pour Tesseract (ex: 'fra+eng').
        psm: Page segmentation mode pour Tesseract.
        conf_thr: Seuil minimal de confiance (0–100).

    Returns:
        DataFrame avec colonnes ['x1','y1','x2','y2','text','conf'],
        ou un DataFrame vide si Tesseract n'est pas disponible
        ou qu'une erreur survient.
    """
    try:
        cfg = f"--oem 1 --psm {psm}"
        df = pytesseract.image_to_data(
            img,
            lang=lang,
            config=cfg,
            output_type=pytesseract.Output.DATAFRAME
        )
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        logger.error("Tesseract binaire introuvable, OCR désactivé", exc_info=True)
        return pd.DataFrame(columns=["x1","y1","x2","y2","text","conf"])
    except Exception:
        logger.exception("Erreur pendant l'appel à pytesseract.image_to_data")
        return pd.DataFrame(columns=["x1","y1","x2","y2","text","conf"])

    # Nettoyage des résultats
    df = df.dropna(subset=["text"]).copy()
    df["conf"] = df["conf"].astype(float)
    df = df[df["conf"] >= conf_thr]
    # Renommage & calcul des coins bas-droite
    df = df.rename(columns={"left": "x1", "top": "y1", "width": "w", "height": "h"})
    df["x2"] = df["x1"] + df["w"]
    df["y2"] = df["y1"] + df["h"]
    return df[["x1", "y1", "x2", "y2", "text", "conf"]]


def test_zoom(
    base_img: Image.Image,
    zoom_factor: float,
    preprocess_fn: Callable[[Image.Image], Image.Image],
    ocr_fn: Callable[..., pd.DataFrame],
    lang: str,
    psm: int,
    conf_thr: int
) -> Optional[Tuple[float, int, float, float, pd.DataFrame, Image.Image]]:
    """
    Teste un facteur de zoom pour l'OCR : renvoie
    (zoom, count, mean_conf, score, df, proc_img) ou None si échec.
    """
    try:
        w, h = base_img.size
        img_z = base_img.resize((int(w * zoom_factor), int(h * zoom_factor)), Image.LANCZOS)
        proc = preprocess_fn(img_z)
        df = ocr_fn(proc, lang, psm, conf_thr)
        cnt = len(df)
        mc = float(df["conf"].mean()) if cnt > 0 else 0.0
        score = cnt * mc
        return (zoom_factor, cnt, mc, score, df, proc)
    except pytesseract.pytesseract.TesseractNotFoundError:
        # On souhaite que cette exception remonte si Tesseract vraiment absent
        raise
    except Exception as e:
        logger.warning(f"Zoom {zoom_factor}× échoué : {e}")
        return None


def find_best_zoom(
    base_img: Image.Image,
    lang: str,
    psm: int,
    conf_thr: int,
    preprocess_fn: Callable[[Image.Image], Image.Image],
    ocr_fn: Callable[..., pd.DataFrame],
    zoom_steps: Optional[List[float]] = None
) -> Tuple[float, int, float, pd.DataFrame, Image.Image, pd.DataFrame]:
    """
    Recherche le meilleur zoom pour maximiser count * mean_conf.
    Ignore les zooms qui lèvent et retombe sur un OCR simple (zoom=1)
    si tous les essais échouent.

    Returns:
        best_zoom, best_count, best_mean_conf,
        best_df, best_proc_img, summary_df
    """
    if zoom_steps is None:
        zoom_steps = [1.0, 2.0, 3.0, 4.0]

    max_workers = min(32, (len(zoom_steps) or 1))
    results: List[Tuple[float, int, float, float, pd.DataFrame, Image.Image]] = []

    # 1) Passage coarse
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(test_zoom, base_img, z, preprocess_fn, ocr_fn, lang, psm, conf_thr)
            for z in zoom_steps
        ]
        for future in futures:
            try:
                res = future.result()
                if res:
                    results.append(res)
            except pytesseract.pytesseract.TesseractNotFoundError:
                # Remonter tant qu'on veut masquer le bouton ailleurs
                raise
            except Exception:
                logger.warning("Un zoom a levé une exception et a été ignoré")

    # 2) Fallback si aucun résultat valide
    if not results:
        logger.error("find_best_zoom : tous les zooms ont échoué, fallback OCR simple")
        proc0 = preprocess_fn(base_img)
        df0 = ocr_fn(proc0, lang, psm, conf_thr)
        cnt0 = len(df0)
        mc0 = float(df0["conf"].mean()) if cnt0 > 0 else 0.0
        summary = pd.DataFrame([{
            "zoom": 1.0,
            "count": cnt0,
            "mean_conf": mc0,
            "score": cnt0 * mc0
        }])
        return (1.0, cnt0, mc0, df0, proc0, summary)

    # 3) Raffinement autour du meilleur initial
    best_initial = max(results, key=lambda x: x[3])[0]
    neighbors = {best_initial}
    if best_initial - 0.5 >= min(zoom_steps):
        neighbors.add(best_initial - 0.5)
    if best_initial + 0.5 <= max(zoom_steps):
        neighbors.add(best_initial + 0.5)

    with ThreadPoolExecutor(max_workers=len(neighbors)) as executor:
        futures = [
            executor.submit(test_zoom, base_img, z, preprocess_fn, ocr_fn, lang, psm, conf_thr)
            for z in sorted(neighbors)
        ]
        for future in futures:
            try:
                res = future.result()
                if res:
                    results.append(res)
            except pytesseract.pytesseract.TesseractNotFoundError:
                raise
            except Exception:
                logger.warning("Un zoom de raffinage a levé et a été ignoré")

    # 4) Choix final
    best_zoom, best_count, best_mean_conf, _, best_df, best_proc_img = max(results, key=lambda x: x[3])

    # 5) Construction du résumé
    summary_df = pd.DataFrame([
        {"zoom": zf, "count": cnt, "mean_conf": mc, "score": sc}
        for (zf, cnt, mc, sc, _, _) in results
    ])

    return (best_zoom, best_count, best_mean_conf, best_df, best_proc_img, summary_df)
