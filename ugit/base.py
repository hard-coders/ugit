import os
from pathlib import Path
from typing import Union, Iterator, Tuple, Dict

from . import data


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


def read_tree(tree_oid: str) -> None:
    for path, oid in get_tree(tree_oid).items():
        path = Path(path)

        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data.get_object(oid))


def is_ignored(path: Union[str, Path]) -> bool:
    return str(data.GIT_DIR) in Path(path).parts
