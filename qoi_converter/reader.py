from PIL.Image import Image

from qoi_converter.chunks import READ_CHUNK_QUEUE
from qoi_converter.utils import ByteReader


def reader(input_stream: bytearray) -> Image:
    result_image: Image
    byte_reader = ByteReader(input_stream)
    while True:
        if byte_reader.read(1):
            for chunk in READ_CHUNK_QUEUE:
                pass
                # TODO
        else:
            break
    return result_image

