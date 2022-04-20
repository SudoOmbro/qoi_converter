from qui_converter.chunks import GenericChunk
from qui_converter.utils import to_u8bit


class CH1(GenericChunk):
    TAG = to_u8bit(0xf0)
    TAG_BIT_MASK = to_u8bit(0xf0)


class CH2(GenericChunk):
    TAG = to_u8bit(0xff)
    TAG_BIT_MASK = to_u8bit(0xff)


def test_mask_test():
    assert CH1.match_tag(to_u8bit(0xf0))
    assert not CH2.match_tag(CH1.TAG)


if __name__ == "__main__":
    test_mask_test()
    byte0 = b"\xfe"
    byte1 = b"\xff"
    print(to_u8bit(byte0[0] - byte1[0]))
