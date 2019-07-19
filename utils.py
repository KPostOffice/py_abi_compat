import os
from typing import Callable
import zipfile
import re
import tempfile
import shutil

def _strings(file_name, n=4):
    with open(file_name, "rb") as f:
        return re.findall(b"([\w \(\)\.:]{4,})", f.read())

def get_gcc_from_whl(zip_file):
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    dirpath = tempfile.mkdtemp()
    zip_ref.extractall(dirpath)
    to_ret = _with_walk_dir(dirpath, get_gcc_vers)
    shutil.rmtree(dirpath)
    return to_ret

def get_gcc_vers(file_name):
    gcc_versions = None
    if check_if_elf(file_name):
        gcc_versions = get_gcc_from_elf(file_name)

    return gcc_versions if gcc_versions != [] else None

def get_gcc_from_elf(elf_file):
    possible_gcc_vers = []
    for word in _strings(elf_file):
        if word.startswith("GCC: ("):
            tokenized = word.split(" ")
            if len(tokenized) > 2 and tokenized[2] not in possible_gcc_vers:
                possible_gcc_vers.append(tokenized[2])

    return possible_gcc_vers

def check_if_elf(file_name):
    with open(file_name, "rb") as f:
        return f.read(24).startswith(b'\x7f\x45\x4c\x46')

def _with_walk_dir(root_dir, to_run):
    for subdir, _, files in os.walk(root_dir):
        for f in files:
            gcc_versions = to_run(os.path.join(subdir, f))
            if gcc_versions != None:
                return gcc_versions
