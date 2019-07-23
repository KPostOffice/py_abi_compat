import os, glob
import subprocess
from functools import partial


## How to determine what arch the so was made for? (8 zeros or 16 zeros)
def get_sys_symbols():
    to_ret = None
    ld_paths = os.environ.get("LD_LIBRARY_PATH")
    if os.path.exists("/usr/lib64"):
        to_ret = _get_lib_dir_symbols("/usr/lib64")
        to_ret.union(_get_lib_dir_symbols("/lib64"))
    elif os.path.exists("/usr/lib32"):
        to_ret = _get_lib_dir_symbols("/usr/lib32", zeros=8)
        to_ret.union(_get_lib_dir_symbols("/lib32", zeros=8))
    elif os.path.exists("/usr/lib"):
        to_ret = _get_lib_dir_symbols("/usr/lib", zeros=8)
        to_ret.union(_get_lib_dir_symbols("/lib", zeros=8))
    else:
        raise FileNotFoundError("No usr libraries were found")

    if ld_paths:
        for path in ld_paths.split(":"):
            to_ret.union(_get_lib_dir_symbols(path))

    os.chdir("/etc/")
    with open("/etc/ld.so.conf", "r") as f:
        for line in f.readlines():
            paths = glob.glob(line[:-1])
            for path in paths:
                with open(path, "r") as conf_file:
                    for conf_path in conf_file.readlines():
                        to_ret.union(_get_lib_dir_symbols(conf_path.strip()))

    return to_ret


def _get_lib_dir_symbols(root_dir, zeros=16):
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