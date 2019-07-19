import elftools
import itertools
import logging
import os
import zipfile
import tempfile
import shutil
from typing import Iterator, Tuple, Optional, Dict, List
from elftools.elf.elffile import ELFFile  # type: ignore
from elftools.common.exceptions import ELFError # type: ignore


def elf_find_versioned_symbols(elf: ELFFile) -> Iterator[Tuple[str, str]]:
    section = elf.get_section_by_name('.gnu.version_r')

    if section is not None:
        for verneed, verneed_iter in section.iter_versions():
            if verneed.name.startswith('ld-linux'):
                continue
            for vernaux in verneed_iter:
                yield (verneed.name, vernaux.name)

def _is_elf(filename: str):
    with open(filename, "rb") as f:
        return f.read(16).startswith(b'\x7f\x45\x4c\x46')

def get_versioned_symbols_from_file(filename: str):
    to_ret = set()
    with open(filename, "rb") as f:
        if not _is_elf(filename):
            return to_ret
        elf = ELFFile(f)
        for _,sym in elf_find_versioned_symbols(elf):
            to_ret.add(sym)
    return to_ret

def get_versioned_symbols_in_dir(root: str):
    to_ret = set({})
    for dirName, subdirList, fileList in os.walk(root):
        for fname in fileList:
            to_ret = to_ret | get_versioned_symbols_from_file(os.path.join(dirName, fname))

    return to_ret

def get_versioned_symbols_from_whl(whl: str):
    tempdir = tempfile.mkdtemp()
    with zipfile.ZipFile(whl, "r") as zip_ref:
        zip_ref.extractall(tempdir)
        to_ret = get_versioned_symbols_in_dir(tempdir)
    
    shutil.rmtree(tempdir)
    return to_ret


if __name__ == "__main__":
    syms = get_versioned_symbols_from_whl("/home/kpostlet/temp/protobuf-3.8.0-cp27-cp27mu-manylinux1_x86_64.whl")
    print(syms)

