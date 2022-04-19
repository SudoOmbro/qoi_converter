import struct
from functools import cache
from typing import List, Iterable, Tuple


@cache
def to_u8bit(num: int):
    if num > 255 or num < 0:
        raise ValueError(f"An unsigned 8 bit integer can't be higher than 255 or lower than 0, value given: {num}")
    return struct.pack("=B", num)


def to_u32bit(num: int):
    return struct.pack("=I", num)


class Pixel:

    def __init__(self, red: int, green: int, blue: int, alpha: int):
        self.r = red
        self.g = green
        self.b = blue
        self.a = alpha
        self.qui_index = self._get_hash()

    def _get_hash(self) -> int:
        return (self.r * 3 + self.g * 5 + self.b * 7 + self.a * 11) % 64

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

    _DEFAULT_PIXEL = Pixel(0, 0, 0, 0)

    def __init__(self):
        self._pixels: List[Pixel] = [self._DEFAULT_PIXEL for _ in range(64)]

    def add(self, pixel: Pixel):
        self._pixels.pop(63)
        self._pixels.insert(0, pixel)

    def __iter__(self) -> Iterable:
        return self._pixels


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
