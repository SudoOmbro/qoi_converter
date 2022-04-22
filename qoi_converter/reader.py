from io import BytesIO

from PIL import Image

from qoi_converter.chunks import READ_CHUNK_QUEUE
from qoi_converter.utils import ByteReader, Context


def read(input_stream: bytes) -> Image:
    # init basic stuff
    byte_reader = ByteReader(input_stream)
    context = Context()
    pixels_buffer = BytesIO()
    # read header
    byte_reader.shift(4)
    width: int = int.from_bytes(byte_reader.read_and_shift(4), "little")
    height: int = int.from_bytes(byte_reader.read_and_shift(4), "little")
    # ignore channels & color space
    byte_reader.shift(2)
    # read pixels
    while True:
        # print("------ New Chunk -----")
        current_byte: bytes = byte_reader.read(1)
        check_end = int.from_bytes(byte_reader.read(4), "little")
        if check_end == 0:
            # print("found end byte")
            break
        for chunk in READ_CHUNK_QUEUE:
            if chunk.match_tag(current_byte):
                chunk.read(context, byte_reader, pixels_buffer)
                break
        else:
            break
    return Image.frombytes("RGBA", (width, height), pixels_buffer.getvalue(), "raw", "RGBA")
