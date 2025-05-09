import pytest
import numpy as np
from PIL import Image
import pandas as pd
from src.ocr import ocr_tess

def make_test_image():
    # Create a simple 100x30 white image with black text using PIL
    img = Image.new('RGB', (100, 30), color='white')
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    # Use a default PIL font
    draw.text((5, 5), "ABC 123", fill='black')
    return img

@pytest.mark.parametrize("conf_thr, expected_min_conf", [
    (0, 0),
    (1, 1)
])
def test_ocr_tess_basic(conf_thr, expected_min_conf):
    img = make_test_image()
    # Run OCR
    df = ocr_tess(img, lang='eng', psm=6, conf_thr=conf_thr)
    # Should return a DataFrame with expected columns
    assert isinstance(df, pd.DataFrame)
    for col in ['x1','y1','x2','y2','text','conf']:
        assert col in df.columns
    # All confidences should be >= threshold
    if not df.empty:
        assert df['conf'].min() >= expected_min_conf
