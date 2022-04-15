from io import BytesIO
from typing import Tuple
from PIL import Image

from qui_converter.utils import to_u8bit, to_u32bit


def write_header(image_size: Tuple[int, int], image_channels: int, image_colorspace: int, destination: BytesIO):
    destination.write(b"qoif")
    destination.write(to_u32bit(image_size[0]))
    destination.write(to_u32bit(image_size[1]))
    destination.write(to_u8bit(image_channels))
    destination.write(to_u8bit(image_colorspace))


def write(image: Image, destination: BytesIO):
    write_header(image.size, image.getbands(), 1, destination)
