from qoi_converter.chunks import GenericChunk
from qoi_converter.utils import to_u8bit, Pixel


class CH1(GenericChunk):
    TAG = to_u8bit(0xf0)
    TAG_BIT_MASK = to_u8bit(0xf0)


class CH2(GenericChunk):
    TAG = to_u8bit(0xff)
    TAG_BIT_MASK = to_u8bit(0xff)


def test_mask_test():
    assert CH1.match_tag(to_u8bit(0xf0))
    assert not CH2.match_tag(CH1.TAG)


def test_pixel_equality():
    p1 = Pixel(0, 0, 0, 255)
    p2 = Pixel(0, 0, 0, 255)
    p3 = Pixel(12, 35, 56, 45)
    assert p1 == p2
    assert p1 != p3


if __name__ == "__main__":
    test_mask_test()
    test_pixel_equality()
    print(Pixel(0, 0, 0, 255).qoi_index)
    print(Pixel(255, 255, 255, 0).qoi_index)

