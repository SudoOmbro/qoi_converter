from qoi_converter.reader import read


def test_read():
    with open("test.qoi", "rb") as file:
        image = read(file.read())
        print(f"pixels: {len(image.getdata())}")
        # for tp in image.getdata():
        #     print(tp)
        image.show("image")


if __name__ == "__main__":
    test_read()
