import itertools
import operator
import os
from collections import namedtuple
from pathlib import Path
from typing import Union, Iterator, Tuple, Dict

from . import data

Commit = namedtuple("Commit", ["tree", "parent", "message"])


def write_tree(directory: Union[str, Path] = ".") -> str:
    """

    :param directory:
    :return: object id
    """
    directory = Path(directory)
    entries = []

    with os.scandir(directory) as it:
        for entry in it:
            full = directory / entry.name

            if is_ignored(full):
                continue

            if entry.is_file(follow_symlinks=False):
                type_ = data.ObjectType.blob
                oid = data.hash_object(full.read_bytes())
            elif entry.is_dir(follow_symlinks=False):
                type_ = data.ObjectType.tree
                oid = write_tree(full)
            entries.append((entry.name, oid, type_))

    tree = "".join(f"{type_} {oid} {name}\n" for name, oid, type_ in sorted(entries))
    return data.hash_object(tree.encode(), data.ObjectType.tree)


def _iter_tree_entries(oid: str) -> Iterator[Tuple[data.ObjectType, str, str]]:
    if not oid:
        return
    tree = data.get_object(oid, data.ObjectType.tree)

    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(maxsplit=2)
        yield type_, oid, name


def get_tree(oid: str, base_path: Union[str, Path] = ".") -> Dict[str, str]:
    """
    :param oid:
    :param base_path:
    :return: Dict[path: str, oid: str]
    """
    result = {}
    base_path = Path(base_path)

    for type_, oid, name in _iter_tree_entries(oid):
        assert "/" not in name
        assert name not in ("..", ".")

        path = base_path / name

        if type_ == data.ObjectType.blob:
            result[str(path)] = oid
        elif type_ == data.ObjectType.tree:
            result.update(get_tree(oid, path))
        else:
            assert False, f"Unknown tree entry {type_}"
    return result


def _empty_current_directory() -> None:
    for root, dirnames, filenames in os.walk(".", topdown=False):
        for filename in filenames:
            path = Path(root) / filename
            if is_ignored(path) or not path.is_file():
                continue
            path.unlink()

        for dirname in dirnames:
            path = Path(root) / dirname
            if is_ignored(path):
                continue

            try:
                path.rmdir()
            except OSError:
                pass


def read_tree(tree_oid: str) -> None:
    _empty_current_directory()

    for path, oid in get_tree(tree_oid).items():
        path = Path(path)

        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data.get_object(oid))


def commit(message: str) -> str:
    """
    :param message: commit message
    :return: object id
    """
    content = f"{data.ObjectType.tree} {write_tree()}\n"
    if head := data.get_ref("HEAD"):
        content += f"parent {head}\n"
    content += f"\n{message}\n"
    oid = data.hash_object(content.encode(), data.ObjectType.commit)

    data.update_ref("HEAD", oid)

    return oid


def checkout(oid: str):
    commit_ = get_commit(oid)
    read_tree(commit_.tree)
    data.update_ref("HEAD", oid)


def get_commit(oid: str) -> Commit:
    tree = None
    parent = None

    commit = data.get_object(oid, "commit").decode()
    lines = commit.splitlines()

    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(" ", 1)
        if key == "tree":
            tree = value
        elif key == "parent":
            parent = value
        else:
            assert False, f"Unknown field {key}"

    message = "\n".join(lines)
    return Commit(tree=tree, parent=parent, message=message)


def create_tag(name: str, oid: str):
    data.update_ref(f"refs/tags/{name}", oid)


def get_oid(name: str):
    return data.get_ref(name) or name


def is_ignored(path: Union[str, Path]) -> bool:
    return str(data.GIT_DIR) in Path(path).parts
