import struct
from functools import cache
from typing import List, Tuple


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

    def compare_rgb(self, pixel: "Pixel") -> int:
        return max((self.r - pixel.r), (self.g - pixel.g), (self.b - pixel.b))

    def compare_rgba(self, pixel: "Pixel"):
        return max(self.compare_rgb(pixel), (self.a - pixel.a))

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


class RunningArray:
    """ A 64 value long hash map that is constantly updated """

    DEFAULT_PIXEL = Pixel(0, 0, 0, 0)

    def __init__(self):
        self._pixels: List[Pixel] = [self.DEFAULT_PIXEL for _ in range(64)]

    def add(self, pixel: Pixel):
        self._pixels[pixel.qoi_index] = pixel

    def get(self, qoi_index: int):
        return self._pixels[qoi_index]


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


class Context:

    def __init__(self, starting_pixel: Pixel):
        self.current_pixel: Pixel = starting_pixel
        self.previous_pixel: Pixel = Pixel(0, 0, 0, 255)
        self.running_array = RunningArray()

    def next_pixel(self, next_pixel: Pixel):
        self.previous_pixel = self.current_pixel
        self.running_array.add(self.current_pixel)
        self.current_pixel = next_pixel
