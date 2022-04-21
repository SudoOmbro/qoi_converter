from io import BytesIO
from typing import Tuple
from PIL import Image

from qoi_converter.utils import to_u8bit, to_u32bit, get_pixels_list, Context
from qoi_converter.chunks import WRITE_CHUNK_QUEUE


def write_header(image_size: Tuple[int, int], image_channels: tuple, image_colorspace: int, destination: BytesIO):
    destination.write(b"qoif")
    destination.write(to_u32bit(image_size[0]))
    destination.write(to_u32bit(image_size[1]))
    destination.write(to_u8bit(len(image_channels)))
    destination.write(to_u8bit(image_colorspace))


def write_stream_end(destination: BytesIO):
    destination.write(to_u32bit(0))
    destination.write(to_u8bit(0))
    destination.write(to_u8bit(0))
    destination.write(to_u8bit(0))
    destination.write(to_u8bit(1))


def write(image: Image, destination: BytesIO):
    write_header(image.size, image.getbands(), 1, destination)
    pixels = get_pixels_list(image)
    context = Context(pixels=pixels)
    while True:
        for chunk in WRITE_CHUNK_QUEUE:
            if chunk.can_be_used(context):
                chunk.write(context, destination)
                break
        if not context.current_pixel:
            break
    write_stream_end(destination)
    print("process ended")
