from io import BytesIO
from typing import List, Type

from qoi_converter.utils import Context, to_u8bit, Pixel, ByteReader, ChunkType, clamp_to_u8bit


class GenericChunk:

    TAG: bytes
    TAG_BIT_MASK: bytes
    TYPE: int

    @classmethod
    def match_tag(cls, input_byte: bytes) -> bool:
        """ returns whether the given byte matches the chunk's tag """
        # print(cls.__name__)
        # print(f"tag: {cls.TAG[0]}, mask: {cls.TAG_BIT_MASK[0]}")
        # print(f"input: {input_byte[0]}, masked input: {input_byte[0] & cls.TAG_BIT_MASK[0]}\n")
        return cls.TAG[0] == (input_byte[0] & cls.TAG_BIT_MASK[0])

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        """ Writes some bytes to the output given the context """
        raise NotImplemented

    @classmethod
    def read(cls, context: Context, reader: ByteReader, output: BytesIO):
        """ Returns a list of pixels given the context """
        raise NotImplemented

    @staticmethod
    def can_be_used(context: Context) -> bool:
        """ returns whether the chunk can be used in writing given the current context """
        return True

    @staticmethod
    def write_pixel(pixel: Pixel, output: BytesIO):
        for byte in pixel.get_rgba_as_u8bit():
            output.write(byte)


class RGBChunk(GenericChunk):

    TAG = to_u8bit(254)
    TAG_BIT_MASK = to_u8bit(255)
    TYPE = ChunkType.QOI_OP_RGB

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        output.write(cls.TAG)
        for byte in context.current_pixel.get_rgb_as_u8bit():
            output.write(byte)
        context.running_array.add(context.current_pixel)
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader, output: BytesIO):
        reader.read_and_shift(1)  # skip the tag
        red: int = reader.read_and_shift(1)[0]
        green: int = reader.read_and_shift(1)[0]
        blue: int = reader.read_and_shift(1)[0]
        context.next_pixel(Pixel(red, green, blue, 255))
        cls.write_pixel(context.current_pixel, output)

    @staticmethod
    def can_be_used(context: Context) -> bool:
        return context.previous_pixel.a == context.current_pixel.a


class RGBAChunk(GenericChunk):

    TAG = to_u8bit(255)
    TAG_BIT_MASK = to_u8bit(255)
    TYPE = ChunkType.QOI_OP_RGBA

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        output.write(cls.TAG)
        for byte in context.current_pixel.get_rgba_as_u8bit():
            output.write(byte)
        context.running_array.add(context.current_pixel)
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader, output: BytesIO):
        reader.read_and_shift(1)  # skip the tag
        red: int = reader.read_and_shift(1)[0]
        green: int = reader.read_and_shift(1)[0]
        blue: int = reader.read_and_shift(1)[0]
        alpha: int = reader.read_and_shift(1)[0]
        context.next_pixel(Pixel(red, green, blue, alpha))
        cls.write_pixel(context.current_pixel, output)


class INDEXChunk(GenericChunk):

    TAG = to_u8bit(0)
    TAG_BIT_MASK = to_u8bit(192)
    TYPE = ChunkType.QOI_OP_INDEX

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        output.write(to_u8bit(context.current_pixel.qoi_index))
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader, output: BytesIO):
        qoi_index = reader.read_and_shift(1)[0]
        context.next_pixel_no_add(context.running_array.get(qoi_index))
        cls.write_pixel(context.running_array.get(qoi_index), output)

    @staticmethod
    def can_be_used(context: Context) -> bool:
        # print(f"{context.running_array}wanted: {context.current_pixel.qoi_index}\n")
        return context.running_array.get(context.current_pixel.qoi_index) == context.current_pixel


class DIFFChunk(GenericChunk):

    TAG = to_u8bit(64)
    TAG_BIT_MASK = to_u8bit(192)
    TYPE = ChunkType.QOI_OP_DIFF

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        r_diff: int = (context.current_pixel.r - context.previous_pixel.r + 2) << 4
        g_diff: int = (context.current_pixel.g - context.previous_pixel.g + 2) << 2
        b_diff: int = context.current_pixel.b - context.previous_pixel.b + 2
        output.write(to_u8bit(cls.TAG[0] + r_diff + g_diff + b_diff))
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader, output: BytesIO):
        byte: int = reader.read_and_shift(1)[0]
        r_diff: int = ((byte & 0x30) >> 4) - 2
        g_diff: int = ((byte & 0x0c) >> 2) - 2
        b_diff: int = (byte & 0x03) - 2
        red: int = clamp_to_u8bit(context.current_pixel.r + r_diff)
        green: int = clamp_to_u8bit(context.current_pixel.g + g_diff)
        blue: int = clamp_to_u8bit(context.current_pixel.b + b_diff)
        context.next_pixel_no_add(Pixel(red, green, blue, context.current_pixel.a))
        cls.write_pixel(context.current_pixel, output)

    @staticmethod
    def can_be_used(context: Context) -> bool:
        if context.current_pixel.a != context.previous_pixel.a:
            return False
        rgb_comparison = context.current_pixel.compare_rgb(context.previous_pixel)
        return (rgb_comparison[0] > -3) and (rgb_comparison[1] < 2)


class LUMAChunk(GenericChunk):

    TAG = to_u8bit(128)
    TAG_BIT_MASK = to_u8bit(192)
    TYPE = ChunkType.QOI_OP_LUMA

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        green_diff: int = context.current_pixel.g - context.previous_pixel.g
        dr_dg: int = ((context.current_pixel.r - context.previous_pixel.r) - green_diff + 8) << 4
        db_dg: int = (context.current_pixel.b - context.previous_pixel.b) - green_diff + 8
        output.write(to_u8bit(cls.TAG[0] + green_diff + 32))
        output.write(to_u8bit(dr_dg + db_dg))
        context.shift_pixel()

    @classmethod
    def read(cls, context: Context, reader: ByteReader, output: BytesIO):
        green_diff: int = reader.read_and_shift(1)[0] - cls.TAG[0] - 32
        second_byte: int = reader.read_and_shift(1)[0]
        dr_dg: int = (second_byte & 0xf0) >> 4
        db_dg: int = second_byte & 0x0f
        cg: int = context.current_pixel.g + green_diff  # current green
        cr: int = dr_dg + context.current_pixel.r + green_diff - 8  # current red
        cb: int = db_dg + context.current_pixel.b + green_diff - 8  # current blue
        context.next_pixel_no_add(Pixel(cr, cg, cb, context.current_pixel.a))
        cls.write_pixel(context.current_pixel, output)

    @staticmethod
    def can_be_used(context: Context) -> bool:
        if context.current_pixel.a != context.previous_pixel.a:
            return False
        green_diff: int = context.current_pixel.g - context.previous_pixel.g
        if (green_diff < -32) or (green_diff > 31):
            return False
        lower_bound: int = green_diff - 9
        upper_bound: int = green_diff + 8
        red_diff: int = context.current_pixel.r - context.previous_pixel.r
        if not (lower_bound < red_diff < upper_bound):
            return False
        blue_diff: int = context.current_pixel.b - context.previous_pixel.b
        if not (lower_bound < blue_diff < upper_bound):
            return False
        return True


class RUNChunk(GenericChunk):

    TAG = to_u8bit(192)
    TAG_BIT_MASK = to_u8bit(192)
    TYPE = ChunkType.QOI_OP_RUN

    @classmethod
    def write(cls, context: Context, output: BytesIO):
        counter: int = 0
        while True:
            if context.current_pixel and (context.current_pixel == context.previous_pixel):
                counter += 1
                context.shift_pixel()
                if counter == 62:
                    break
            else:
                break
        output.write(to_u8bit(cls.TAG[0] + counter - 1))

    @classmethod
    def read(cls, context: Context, reader: ByteReader, output: BytesIO):
        read_byte: int = reader.read_and_shift(1)[0]
        for _ in range(read_byte - cls.TAG[0] + 1):
            cls.write_pixel(context.current_pixel, output)
        context.next_pixel_no_add(context.current_pixel)

    @staticmethod
    def can_be_used(context: Context) -> bool:
        try:
            return context.previous_pixel == context.current_pixel == context.pixels[context.array_position + 1]
        except Exception as e:
            print(e)
            return False


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
