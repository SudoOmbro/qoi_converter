import struct


def to_u8bit(num: int):
    return struct.pack("=B", num)


def to_u32bit(num: int):
    return struct.pack("=I", num)
