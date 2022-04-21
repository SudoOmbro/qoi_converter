from io import BytesIO

from qoi_converter.writer import write_header, write
from PIL import Image


def test_header_size():
    test_buffer = BytesIO()
    write_header((500, 200), ('R', 'G', 'B'), 1, test_buffer)
    assert len(test_buffer.getvalue()) == 14


def test_write():
    test_input = Image.open("test_image.png", "r").convert("RGBA")
    test_output = BytesIO()
    write(test_input, test_output)
    with open("test.qoi", "wb") as file:
        file.write(test_output.getvalue())


if __name__ == "__main__":
    test_header_size()
    test_write()
