from io import BytesIO
from typing import List, Type

from qui_converter.utils import Context, to_u8bit, Pixel, ByteReader


class ChuckType:

    QOI_OP_RGB = 0
    QOI_OP_RGBA = 1
    QOI_OP_INDEX = 2
    QOI_OP_DIFF = 3
    QOI_OP_LUMA = 4
    QOI_OP_RUN = 5


class GenericChuck:

    TAG: bytes
    TAG_BIT_MASK: bytes
    NAME: str

    @classmethod
    def test_tag(cls, input_byte: bytes) -> bool:
        """ returns whether the given byte contains the chunk's tag """
        return cls.TAG == (input_byte[0] & cls.TAG_BIT_MASK[0])

    @staticmethod
    def write(context: Context, output: BytesIO):
        """ Writes some bytes to the output given the context """
        raise NotImplemented

    @staticmethod
    def read(context: Context, reader: ByteReader) -> List[Pixel]:
        """ Returns a list of pixels given the context """
        raise NotImplemented


CHUNKS: List[Type[GenericChuck]] = []


def add_to_list_of_chunks(chunk_type: Type[GenericChuck]) -> Type[GenericChuck]:
    CHUNKS.append(chunk_type)
    return chunk_type


@add_to_list_of_chunks
class RGBChunk(GenericChuck):

    TAG = to_u8bit(254)
    TAG_BIT_MASK = to_u8bit(255)
    NAME = "QOI_OP_RGB"

    @staticmethod
    def write(context: Context, output: BytesIO):
        output.write(RGBChunk.TAG)
        for byte in context.current_pixel.get_rgb_as_u8bit():
            output.write(byte)

    @staticmethod
    def read(context: Context, reader: ByteReader) -> List[Pixel]:
        reader.read_and_shift(1)  # skip the tag
        red: int = int(reader.read_and_shift(1))
        green: int = int(reader.read_and_shift(1))
        blue: int = int(reader.read_and_shift(1))
        context.next_pixel(Pixel(red, green, blue, 255))
        return [context.current_pixel]


@add_to_list_of_chunks
class RGBAChunk(GenericChuck):

    TAG = to_u8bit(255)
    TAG_BIT_MASK = to_u8bit(255)
    NAME = "QOI_OP_RGBA"

    @staticmethod
    def write(context: Context, output: BytesIO):
        output.write(RGBChunk.TAG)
        for byte in context.current_pixel.get_rgba_as_u8bit():
            output.write(byte)

    @staticmethod
    def read(context: Context, reader: ByteReader) -> List[Pixel]:
        reader.read_and_shift(1)  # skip the tag
        red: int = int(reader.read_and_shift(1))
        green: int = int(reader.read_and_shift(1))
        blue: int = int(reader.read_and_shift(1))
        alpha: int = int(reader.read_and_shift(1))
        context.next_pixel(Pixel(red, green, blue, alpha))
        return [context.current_pixel]
