from docx import Document
from PIL import Image

from graded_roof.manuscript import _enforce_ascii


def test_ascii_normalization_preserves_embedded_images(tmp_path):
    image_path = tmp_path / "figure.png"
    Image.new("RGB", (20, 20), "white").save(image_path)
    document = Document()
    document.add_paragraph("modeled–result")
    document.add_picture(str(image_path))

    _enforce_ascii(document)

    assert document.paragraphs[0].text == "modeled-result"
    assert len(document.inline_shapes) == 1
