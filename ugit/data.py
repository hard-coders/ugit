import hashlib
import os
from enum import Enum

from pathlib import Path
from typing import Iterator, Tuple, Generator

GIT_DIR = Path(".ugit")
GIT_OBJECTS_DIR = GIT_DIR / "objects"
GIT_REFS_DIR = GIT_DIR / "refs"


class ObjectType(str, Enum):
    blob = "blob"
    tree = "tree"
    commit = "commit"


def init() -> None:
    GIT_DIR.mkdir(exist_ok=True)
    GIT_OBJECTS_DIR.mkdir()


def update_ref(ref: str, oid: str) -> None:
    ref_path = GIT_DIR / ref
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    ref_path.write_text(oid)


def get_ref(ref: str) -> str:
    ref_path = GIT_DIR / ref
    value = None
    if ref_path.is_file():
        value = ref_path.read_text().strip()

    if value and value.startswith("ref:"):
        return get_ref(value.split(":", 1)[1].strip())

    return value


def iter_refs() -> Generator[Tuple[str, str], None, None]:
    refs = ["HEAD"]
    for root, _, filenames in os.walk(GIT_REFS_DIR):
        root = Path(root).relative_to(GIT_DIR)
        refs.extend(str(root / name) for name in filenames)

    for ref_name in refs:
        yield ref_name, get_ref(ref_name)


def hash_object(data: bytes, type_=ObjectType.blob) -> str:
    obj = type_.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()

    (GIT_OBJECTS_DIR / oid).write_bytes(obj)

    return oid


def get_object(oid: str, expected=ObjectType.blob) -> bytes:
    obj = (GIT_OBJECTS_DIR / oid).read_bytes()

    type_, _, data = obj.partition(b"\x00")
    type_ = type_.decode()

    if expected is not None:
        assert type_ == expected, f"Expected {expected}, got {type_}"
    return data
