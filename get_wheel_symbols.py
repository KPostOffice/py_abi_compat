import elftools
import tarfile
import itertools
import logging
import os
import zipfile
import tempfile
import shutil
from typing import Iterator, Tuple, Optional, Dict, List
from elftools.elf.elffile import ELFFile  # type: ignore
from elftools.common.exceptions import ELFError # type: ignore
from packaging import version

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
    try:
        with zipfile.ZipFile(whl, "r") as zip_ref:
            zip_ref.extractall(tempdir)
            to_ret = get_versioned_symbols_in_dir(tempdir)
    except:
        tf = tarfile.open(whl)
        tf.extractall(tempdir)
        to_ret = get_versioned_symbols_in_dir(tempdir)
    
    shutil.rmtree(tempdir)
    return to_ret


"""
This function returns a tuple. 1 in position 0 represents GCC < 5,
1 in position 1 represents GCC > 5 these two are incompatible so it's enough
generate a representative tuple for each wheel file and do an elementwise sum.
If neither position is zero, then it may fail due to CXX11 ABI incompatability
"""
def gcc_version_from_cpp_syms(symbols: set) -> list:
    to_ret = [0, 0]
    for sym in symbols:
        s = sym.split("_")
        if s[0] == "GLIBCXX":
            if version.parse(s[1]) < version.parse("3.4.21"):
                to_ret[0] = 1
            else:
                to_ret[1] = 1
        elif s[0] == "CXXABI":
            if version.parse(s[1]) < version.parse("1.3.9"):
                to_ret[0] = 1
            else:
                to_ret[1] = 1

    return to_ret

if __name__ == "__main__":
    syms = get_versioned_symbols_from_whl("/home/kpostlet/temp/protobuf-3.8.0-cp27-cp27mu-manylinux1_x86_64.whl")
    print(syms)

