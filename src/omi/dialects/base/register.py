from omi.dialects.base.dialect import Dialect

DIALECT_DICT = {}


def register(identifier: str):
    def inner(dialect_class: Dialect):
        DIALECT_DICT[identifier] = dialect_class
        return dialect_class

    return inner


def get_dialect(identifier: str) -> Dialect:
    return DIALECT_DICT[identifier]
