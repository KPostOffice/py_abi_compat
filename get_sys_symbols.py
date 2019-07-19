import os
import subprocess
from functools import partial

def get_sys_symbols():
    to_ret = None
    if os.path.exists("/usr/lib64"):
        to_ret = _get_lib_symbols("/usr/lib64")
        to_ret.union(_get_lib_symbols("/lib64"))
    elif os.path.exists("/usr/lib32"):
        to_ret = _get_lib_symbols("/usr/lib32", zeros=8)
        to_ret.union(_get_lib_symbols("/lib32", zeros=8))
    elif os.path.exists("/usr/lib"):
        to_ret = _get_lib_symbols("/usr/lib", zeros=8)
        to_ret.union(_get_lib_symbols("/lib", zeros=8))
    else:
        raise FileNotFoundError("No usr libraries were found")

    return to_ret

def _get_lib_symbols(root_dir, zeros=16):
    to_ret = set({})
    zero_string = "0" * zeros
    command = f"nm -D {root_dir}/*.so* | grep {zero_string}"
    out = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).stdout.read()
    lines = out.split(b'\n')
    for line in lines:
        columns = line.split(b' ')
        if len(columns) > 2:
            to_ret.add(columns[2])

    return to_ret

def _with_dir_files(root_dir, to_run, accumulator):
    for f in os.listdir(root_dir):
        accumulator.update(to_run(os.path.join(root_dir, f)))

if __name__=="__main__":
    print(get_sys_symbols())