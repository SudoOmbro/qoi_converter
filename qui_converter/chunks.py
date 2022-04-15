from qui_converter.utils import Context


class GenericChuck:

    TAG: int
    TAG_LENGTH: int

    def generate(self, context: Context):
        raise NotImplemented

    def read(self, context: Context):
        raise NotImplemented
