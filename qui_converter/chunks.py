from io import BytesIO
from typing import List, Type

from qui_converter.utils import Context, to_u8bit, Pixel, ByteReader, ChunkType


class GenericChunk:

    TAG: bytes
    TAG_BIT_MASK: bytes
    TYPE: int

    @classmethod
    def match_tag(cls, input_byte: bytes) -> bool:
        """ returns whether the given byte matches the chunk's tag """
        return cls.TAG == to_u8bit(input_byte[0] & cls.TAG_BIT_MASK[0])

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        """ Writes some bytes to the output given the context """
        context.previous_chunk_type = cls.TYPE

    @classmethod
    def read(cls, context: Context, reader: ByteReader) -> List[Pixel]:
        """ Returns a list of pixels given the context """
        raise NotImplemented

    @staticmethod
    def can_be_used(context: Context) -> bool:
        """ returns whether the chunk can be used in writing given the current context """
        return True


class RGBChunk(GenericChunk):

    TAG = to_u8bit(254)
    TAG_BIT_MASK = to_u8bit(255)
    TYPE = ChunkType.QOI_OP_RGB

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        super().write(context, output)
        output.write(RGBChunk.TAG)
        for byte in context.current_pixel.get_rgb_as_u8bit():
            output.write(byte)
        context.running_array.add(context.current_pixel)
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader) -> List[Pixel]:
        reader.read_and_shift(1)  # skip the tag
        red: int = reader.read_and_shift(1)[0]
        green: int = reader.read_and_shift(1)[0]
        blue: int = reader.read_and_shift(1)[0]
        context.next_pixel(Pixel(red, green, blue, 255))
        return [context.current_pixel]

    @staticmethod
    def can_be_used(context: Context) -> bool:
        return context.previous_pixel.a == context.current_pixel.a


class RGBAChunk(GenericChunk):

    TAG = to_u8bit(255)
    TAG_BIT_MASK = to_u8bit(255)
    TYPE = ChunkType.QOI_OP_RGBA

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        super().write(context, output)
        output.write(RGBChunk.TAG)
        for byte in context.current_pixel.get_rgba_as_u8bit():
            output.write(byte)
        context.running_array.add(context.current_pixel)
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader) -> List[Pixel]:
        reader.read_and_shift(1)  # skip the tag
        red: int = reader.read_and_shift(1)[0]
        green: int = reader.read_and_shift(1)[0]
        blue: int = reader.read_and_shift(1)[0]
        alpha: int = reader.read_and_shift(1)[0]
        context.next_pixel(Pixel(red, green, blue, alpha))
        return [context.current_pixel]


class INDEXChunk(GenericChunk):

    TAG = to_u8bit(0)
    TAG_BIT_MASK = to_u8bit(192)
    TYPE = ChunkType.QOI_OP_INDEX

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        super().write(context, output)
        output.write(to_u8bit(context.current_pixel.qoi_index))
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader) -> List[Pixel]:
        qoi_index = reader.read_and_shift(1)[0]
        return [context.running_array.get(qoi_index)]

    @staticmethod
    def can_be_used(context: Context) -> bool:
        return context.running_array.get(context.current_pixel.qoi_index) == context.current_pixel


class DIFFChunk(GenericChunk):

    TAG = to_u8bit(64)
    TAG_BIT_MASK = to_u8bit(192)
    TYPE = ChunkType.QOI_OP_DIFF

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        super().write(context, output)
        r_diff: int = (context.current_pixel.r - context.previous_pixel.r + 2) << 4
        g_diff: int = (context.current_pixel.g - context.previous_pixel.g + 2) << 2
        b_diff: int = context.current_pixel.b - context.previous_pixel.b + 2
        output.write(to_u8bit(DIFFChunk.TAG[0] + r_diff + g_diff + b_diff))
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader) -> List[Pixel]:
        # TODO
        return [context.current_pixel]

    @staticmethod
    def can_be_used(context: Context) -> bool:
        if context.current_pixel.a != context.previous_pixel.a:
            return False
        rgb_comparison = context.current_pixel.compare_rgb(context.previous_pixel)
        if (rgb_comparison[0] > -2) and (rgb_comparison[1] < 3):
            return True
        return False


class LUMAChunk(GenericChunk):

    TAG = to_u8bit(128)
    TAG_BIT_MASK = to_u8bit(192)
    TYPE = ChunkType.QOI_OP_LUMA

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        super().write(context, output)
        green_diff: int = context.current_pixel.g - context.previous_pixel.g
        dr_dg: int = ((context.current_pixel.r - context.previous_pixel.r) - green_diff + 8) << 4
        db_dg: int = (context.current_pixel.b - context.previous_pixel.b) - green_diff + 8
        output.write(to_u8bit(DIFFChunk.TAG[0] + green_diff + 32))
        output.write(to_u8bit(dr_dg + db_dg))
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader) -> List[Pixel]:
        # TODO
        return [context.current_pixel]

    @staticmethod
    def can_be_used(context: Context) -> bool:
        if context.current_pixel.a != context.previous_pixel.a:
            return False
        rgb_comparison = context.current_pixel.compare_rgb(context.previous_pixel)
        if (rgb_comparison[0] > -33) and (rgb_comparison[1] < 32):
            return True
        return False


class RUNChunk(GenericChunk):

    TAG = to_u8bit(192)
    TAG_BIT_MASK = to_u8bit(192)
    TYPE = ChunkType.QOI_OP_RUN

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        super().write(context, output)
        counter: int = 0
        while True:
            if context.current_pixel == context.previous_pixel:
                counter += 1
                context.shift_pixel()
                if counter == 62:
                    break
            else:
                break
        output.write(to_u8bit(cls.TAG[0] + counter - 1))

    @classmethod
    def read(cls, context: Context, reader: ByteReader) -> List[Pixel]:
        read_byte: int = reader.read_and_shift(1)[0]
        return [context.previous_pixel for _ in range(read_byte - cls.TAG[0] + 1)]

    @staticmethod
    def can_be_used(context: Context) -> bool:
        return context.previous_pixel == context.current_pixel == context.pixels[context.array_position + 1]


# Chunk queues, determine the priority of each chunk on the others while writing/reading

WRITE_CHUNK_QUEUE: List[Type[GenericChunk]] = [
    RUNChunk,
    INDEXChunk,
    DIFFChunk,
    LUMAChunk,
    RGBChunk,
    RGBAChunk
]

READ_CHUNK_QUEUE: List[Type[GenericChunk]] = [
    RGBAChunk,
    RGBChunk,
    INDEXChunk,
    DIFFChunk,
    LUMAChunk,
    RUNChunk
]
