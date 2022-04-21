import struct
from functools import cache
from typing import List, Tuple

from PIL.Image import Image


@cache
def to_u8bit(num: int):
    if num < 0:
        num = 256 + num
    return struct.pack("=B", num)


def to_u32bit(num: int):
    if num < 0:
        num = 4294967296 + num
    return struct.pack("=I", num)


class Pixel:

    def __init__(self, red: int, green: int, blue: int, alpha: int):
        self.r = red
        self.g = green
        self.b = blue
        self.a = alpha
        self.qoi_index = self._get_hash()

    def _get_hash(self) -> int:
        return (self.r * 3 + self.g * 5 + self.b * 7 + self.a * 11) % 64

    def compare_rgb(self, pixel: "Pixel") -> Tuple[int, int]:
        differences = (self.r - pixel.r), (self.g - pixel.g), (self.b - pixel.b)
        return min(differences), max(differences)

    def compare_rgba(self, pixel: "Pixel") -> Tuple[int, int]:
        differences = (self.r - pixel.r), (self.g - pixel.g), (self.b - pixel.b), (self.a - pixel.a)
        return min(differences), max(differences)

    def get_rgb_as_u8bit(self) -> Tuple[bytes, bytes, bytes]:
        return (
            to_u8bit(self.r),
            to_u8bit(self.g),
            to_u8bit(self.b)
        )

    def get_rgba_as_u8bit(self) -> Tuple[bytes, bytes, bytes, bytes]:
        return (
            to_u8bit(self.r),
            to_u8bit(self.g),
            to_u8bit(self.b),
            to_u8bit(self.a)
        )

    def __eq__(self, other: "Pixel"):
        return self.compare_rgba(other) == (0, 0)

    def __str__(self):
        return f"rgb: {self.r} {self.g} {self.b}, alpha: {self.a}"


def get_pixels_list(image: Image) -> List[Pixel]:
    image_data = image.getdata()
    pixels_list: List[Pixel] = []
    for tp in image_data:
        pixels_list.append(Pixel(tp[0], tp[1], tp[2], tp[3]))
    return pixels_list


class RunningArray:
    """ A 64 value long hash map that is constantly updated """

    DEFAULT_PIXEL = Pixel(0, 0, 0, 0)

    def __init__(self):
        self._pixels: List[Pixel] = [self.DEFAULT_PIXEL for _ in range(64)]

    def add(self, pixel: Pixel):
        self._pixels[pixel.qoi_index] = pixel

    def get(self, qoi_index: int):
        return self._pixels[qoi_index]

    def __str__(self):
        output: str = ""
        index: int = 0
        for pixel in self._pixels:
            if pixel is not self.DEFAULT_PIXEL:
                output += f"{index}: ({pixel})\n"
            index += 1
        return output


class ByteReader:

    def __init__(self, array: bytearray):
        self.array = array
        self._offset = 0

    def read(self, number_of_bytes: int) -> bytes:
        """ reads number_of_bytes bytes from the given array at the current offset & returns them """
        return self.array[self._offset:self._offset + number_of_bytes]

    def shift(self, number_of_bytes: int):
        """ shifts the offset ahead by number_of_bytes bytes """
        self._offset += number_of_bytes

    def move(self, offset: int):
        """ moves the offset to offset """
        self._offset = offset

    def read_and_shift(self, number_of_bytes: int) -> bytes:
        result = self.read(number_of_bytes)
        self.shift(number_of_bytes)
        return result


class ChunkType:
    QOI_OP_RGB = 0
    QOI_OP_RGBA = 1
    QOI_OP_INDEX = 2
    QOI_OP_DIFF = 3
    QOI_OP_LUMA = 4
    QOI_OP_RUN = 5


class Context:

    def __init__(self, pixels: List[Pixel] or None = None):
        self.pixels = pixels
        self.array_position: int = 0
        self.current_pixel: Pixel = pixels[0] if pixels else None
        self.previous_pixel: Pixel = Pixel(0, 0, 0, 255)
        self.running_array = RunningArray()
        self.previous_chunk_type: int = ChunkType.QOI_OP_RGBA

    def next_pixel(self, next_pixel: Pixel):
        """ manually set the next pixel, useful when reading """
        self.previous_pixel = self.current_pixel
        self.running_array.add(self.current_pixel)
        self.current_pixel = next_pixel

    def shift_pixel(self):
        """ shift in the array of pixels, useful for writing """
        self.array_position += 1
        try:
            next_pixel = self.pixels[self.array_position]
        except Exception as e:
            next_pixel = None
            print(e)
        self.previous_pixel = self.current_pixel
        self.current_pixel = next_pixel
