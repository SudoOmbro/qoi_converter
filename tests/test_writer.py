from io import BytesIO

from qui_converter.writer import write_header


def test_header_size():
    test_buffer = BytesIO()
    write_header((500, 200), 4, 1, test_buffer)
    assert len(test_buffer.getvalue()) == 14


if __name__ == "__main__":
    test_header_size()
