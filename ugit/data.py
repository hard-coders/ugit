import hashlib
from pathlib import Path


GIT_DIR = Path(".ugit")
GIT_OBJECTS_DIR = GIT_DIR / Path("objects")


def init():
    GIT_DIR.mkdir(exist_ok=True)
    GIT_OBJECTS_DIR.mkdir()


def hash_object(data):
    oid = hashlib.sha1(data).hexdigest()
    with open(f"{GIT_OBJECTS_DIR}/{oid}", "wb") as out:
        out.write(data)
    return oid
