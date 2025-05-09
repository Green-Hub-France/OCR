import os
import io
import pytest
import pandas as pd
from PIL import Image
import fitz

from src.preprocessing import preprocess
from src.ocr import ocr_tess, find_best_zoom
from src.textract_service import textract_parse
from src.utils import extract_entities_ocr

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
PDF_FILE = os.path.join(FIXTURES_DIR, 'Facture.pdf')
IMAGE_FILE = os.path.join(FIXTURES_DIR, 'Facture.png')  # optionally provide

@pytest.fixture(scope='module')
def pdf_image():
    # Load first page of PDF as PIL Image
    raw = open(PDF_FILE, 'rb').read()
    doc = fitz.open(stream=raw, filetype='pdf')
    pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(2, 2))
    mode = 'RGB' if pix.n < 4 else 'RGBA'
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples).convert('RGB')
    return img

@pytest.fixture(scope='module')
def sample_image():
    # Optional: load a separate image fixture if needed
    if os.path.exists(IMAGE_FILE):
        return Image.open(IMAGE_FILE).convert('RGB')
    pytest.skip("No standalone image fixture available")


def test_textract_e2e(pdf_image):
    # Convert PIL image to bytes
    buf = io.BytesIO()
    pdf_image.save(buf, format='PNG')
    img_bytes = buf.getvalue()

    kvs = textract_parse(img_bytes)
    assert isinstance(kvs, dict)
    assert len(kvs) > 0, "Expected at least one key-value pair from Textract"


def test_ocr_e2e(pdf_image):
    # Preprocess and run OCR
    proc = preprocess(pdf_image)
    df = ocr_tess(proc, lang='fra+eng', psm=6, conf_thr=30)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty, "Expected OCR DataFrame to have at least one row"


def test_extract_entities(pdf_image):
    # Run OCR then extract entities
    proc = preprocess(pdf_image)
    df = ocr_tess(proc, lang='fra+eng', psm=6, conf_thr=30)
    text = " ".join(df['text'].tolist())
    entities = extract_entities_ocr(text)
    assert isinstance(entities, dict)
    # Expect an invoice number pattern
    assert entities.get('invoice_number') is not None


def test_find_best_zoom(pdf_image):
    # Test zoom search
    z, cnt, mc, df_best, img_proc, summary = find_best_zoom(
        pdf_image, 'fra+eng', 6, 30, preprocess, ocr_tess
    )
    assert isinstance(z, float)
    assert isinstance(cnt, int)
    assert isinstance(mc, float)
    assert isinstance(df_best, pd.DataFrame)
    assert isinstance(summary, pd.DataFrame)
    assert not summary.empty, "Expected summary DataFrame to have rows"


def test_csv_generation(pdf_image, tmp_path):
    # Ensure CSV can be generated and saved
    proc = preprocess(pdf_image)
    df = ocr_tess(proc, lang='fra+eng', psm=6, conf_thr=30)
    csv_path = tmp_path / "ocr_output.csv"
    df.to_csv(csv_path, index=False)
    assert csv_path.exists()
    # Read back and verify columns
    df2 = pd.read_csv(csv_path)
    for col in ['x1','y1','x2','y2','text','conf']:
        assert col in df2.columns
