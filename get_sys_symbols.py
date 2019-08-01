import os, glob
import subprocess
from functools import partial
from typing import Dict, List
from thoth.analyzer import run_command
from thoth.common import cwd
import logging

_LOGGER = logging.getLogger(__name__)

def get_system_symbols() -> Dict[str, List[str]]:
    """Get library symbols found in relevant directories, configuration and environment variables."""
    result = {}
    _get_lib_dir_symbols(result, "/usr/lib64")
    _get_lib_dir_symbols(result, "/lib64")
    _get_lib_dir_symbols(result, "/usr/lib32")
    _get_lib_dir_symbols(result, "/lib32")
    _get_lib_dir_symbols(result, "/usr/lib")
    _get_lib_dir_symbols(result, "/lib")
    _ld_config_symbols(result, "/etc/ld.so.conf")
    _ld_env_symbols(result)
    # Convert to list as a result, also good for serialization into JSON happening later on.
    return {path: list(symbols) for path, symbols in result.items()}

def _ld_env_symbols(result: dict) -> None:
    """Gather library symbols based on entries in LD_LIBRARY_PATH environment variable."""
    ld_paths = os.getenv("LD_LIBRARY_PATH")

    if ld_paths is None:
        _LOGGER.debug("No LD_LIBRARY_PATH detected to gather system symbols")
        return

    for p in ld_paths.split(":"):
        _get_lib_dir_symbols(result, p)

def _ld_config_symbols(result: dict, path: str) -> None:
    """Gather library symbols based on conf path."""
    head, tail = os.path.split(path)
    try:
        with cwd(head), open(tail, "r") as f:
            for line in f.readlines():
                if line.startswith("include "):
                    line = line[len("include "):]
                    _ld_config_symbols(line)
                    continue
                
                if not line:
                    continue

                # Both relative and absolute will work:
                #   os.path.join("/foo", "bar") == "/foo/bar"
                #   os.path.join("/foo", "/bar") == "/bar"
                for entry_path in glob.glob(os.path.join(head, line.strip())):
                    with open(os.path.join(path, entry_path), "r") as conf_file:
                        for conf_path in conf_file.readlines():
                            _get_lib_dir_symbols(result, conf_path)
    except Exception as exc:
        _LOGGER.warning("Cannot load symbols based on ld.so.conf: %s", str(exc))

def _get_lib_dir_symbols(result, root_dir):
    """Get library symbols from a directory."""
    for so_file_path in glob.glob(os.path.join(root_dir, "*.so*")):
        # We grep for '0 A' here because all exported symbols are outputted by nm like:
        # 00000000 A GLIBC_1.x or:
        # 0000000000000000 A GLIBC_1.x
        command = f"nm -D {so_file_path!r} | grep '0 A'"

        # Drop path to the extracted container in the output.
        so_file_path = so_file_path[len(root_dir)+1:]

        _LOGGER.debug("Gathering symbols from %r", so_file_path)
        command_result = run_command(command, timeout=120, raise_on_error=False)
        if command_result.return_code != 0:
            _LOGGER.warning(
                "Failed to obtain library symbols from %r; stderr: %s, stdout: %s",
                so_file_path,
                command_result.stderr,
                command_result.stdout
            )
            continue

        if so_file_path not in result:
            result[so_file_path] = set()

        for line in command_result.stdout.splitlines():
            columns = line.split(' ')
            if len(columns) > 2:
                result[so_file_path].add(columns[2])

def get_sym_versions(sym_str: str, syms: set):
    to_ret = []
    for s in syms:
        x = s.split("_")
        if x[0] == sym_str:
            to_ret.append(x[1])

    to_ret.sort()
    return to_ret

if __name__=="__main__":
    s = get_system_symbols()
    print(s)
