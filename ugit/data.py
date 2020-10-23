import hashlib
from enum import Enum

from pathlib import Path


GIT_DIR = Path(".ugit")
GIT_OBJECTS_DIR = GIT_DIR / Path("objects")


class ObjectType(str, Enum):
    blob = "blob"
    tree = "tree"


def init() -> None:
    GIT_DIR.mkdir(exist_ok=True)
    GIT_OBJECTS_DIR.mkdir()


def hash_object(data: bytes, type_=ObjectType.blob) -> str:
    obj = type_.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()

    with open(GIT_OBJECTS_DIR / oid, "wb") as out:
        out.write(obj)
    return oid


def get_object(oid: str, expected=ObjectType.blob) -> bytes:
    with open(GIT_OBJECTS_DIR / oid, "rb") as f:
        obj = f.read()

        type_, _, data = obj.partition(b"\x00")
        type_ = type_.decode()

        if expected is not None:
            assert type_ == expected, f"Expected {expected}, got {type_}"
        return data
