from io import BytesIO
from typing import List, Type

from qui_converter.utils import Context, to_u8bit, Pixel, ByteReader, RunningArray


class GenericChunk:

    TAG: bytes
    TAG_BIT_MASK: bytes
    NAME: str

    @classmethod
    def match_tag(cls, input_byte: bytes) -> bool:
        """ returns whether the given byte matches the chunk's tag """
        return cls.TAG == to_u8bit(input_byte[0] & cls.TAG_BIT_MASK[0])

    @staticmethod
    def write(context: Context, output: BytesIO):
        """ Writes some bytes to the output given the context """
        raise NotImplemented

    @staticmethod
    def read(context: Context, reader: ByteReader) -> List[Pixel]:
        """ Returns a list of pixels given the context """
        raise NotImplemented

    @staticmethod
    def can_be_used(context: Context) -> bool:
        """ returns whether the chunk can be used in writing given the current context """
        return True


CHUNKS: List[Type[GenericChunk]] = []


def add_to_list_of_chunks(chunk_type: Type[GenericChunk]) -> Type[GenericChunk]:
    CHUNKS.append(chunk_type)
    return chunk_type


@add_to_list_of_chunks
class RGBChunk(GenericChunk):

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
        red: int = reader.read_and_shift(1)[0]
        green: int = reader.read_and_shift(1)[0]
        blue: int = reader.read_and_shift(1)[0]
        context.next_pixel(Pixel(red, green, blue, 255))
        return [context.current_pixel]


@add_to_list_of_chunks
class RGBAChunk(GenericChunk):

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
        red: int = reader.read_and_shift(1)[0]
        green: int = reader.read_and_shift(1)[0]
        blue: int = reader.read_and_shift(1)[0]
        alpha: int = reader.read_and_shift(1)[0]
        context.next_pixel(Pixel(red, green, blue, alpha))
        return [context.current_pixel]


@add_to_list_of_chunks
class INDEXChunk(GenericChunk):

    TAG = to_u8bit(0)
    TAG_BIT_MASK = to_u8bit(192)
    NAME = "QOI_OP_INDEX"

    @staticmethod
    def write(context: Context, output: BytesIO):
        output.write(to_u8bit(context.current_pixel.qoi_index))

    @staticmethod
    def read(context: Context, reader: ByteReader) -> List[Pixel]:
        qoi_index = reader.read_and_shift(1)[0]
        return [context.running_array.get(qoi_index)]

    @staticmethod
    def can_be_used(context: Context) -> bool:
        return context.running_array.get(context.current_pixel.qoi_index).compare_rgba(context.current_pixel) == 0


@add_to_list_of_chunks
class DIFFChunk(GenericChunk):

    TAG = to_u8bit(64)
    TAG_BIT_MASK = to_u8bit(192)
    NAME = "QOI_OP_DIFF"

    @staticmethod
    def write(context: Context, output: BytesIO):
        r_diff: int = (context.current_pixel.r - context.previous_pixel.r + 2) << 4
        g_diff: int = (context.current_pixel.g - context.previous_pixel.g + 2) << 2
        b_diff: int = context.current_pixel.b - context.previous_pixel.b + 2
        output.write(to_u8bit(DIFFChunk.TAG[0] + r_diff + g_diff + b_diff))

    @staticmethod
    def read(context: Context, reader: ByteReader) -> List[Pixel]:
        # TODO
        return [context.current_pixel]

    @staticmethod
    def can_be_used(context: Context) -> bool:
        if context.current_pixel.a != context.previous_pixel.a:
            return False
        rgb_comparison = context.current_pixel.compare_rgb(context.previous_pixel)
        if -2 <= rgb_comparison <= 1:
            return True
