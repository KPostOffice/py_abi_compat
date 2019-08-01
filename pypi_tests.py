import get_wheel_symbols
from pprint import PrettyPrinter
import json
import requests
import tempfile
import subprocess
import os

def get_top_packages(n=100):
    response = requests.get("https://hugovk.github.io/top-pypi-packages/top-pypi-packages-365-days.json")
    json_data = json.loads(response.text)
    return [x["project"] for x in json_data["rows"][:n]]

def get_top_package_symbols(result, n=100):
    for package in get_top_packages(n):
        dirpath = tempfile.mkdtemp()
        subprocess.run(["pip", "download", package, "--no-deps", "-d", dirpath])
        for f in os.listdir(dirpath):
            result[package] = get_wheel_symbols.get_versioned_symbols_from_whl(os.path.join(dirpath, f))

if __name__=="__main__":
    for package in get_top_packages(300):
        dirpath = tempfile.mkdtemp()
        subprocess.run(["pip", "download", package, "--no-deps", "-d", dirpath])
        for f in os.listdir(dirpath):
            s = get_wheel_symbols.get_versioned_symbols_from_whl(os.path.join(dirpath, f))
        print(get_wheel_symbols.gcc_version_from_cpp_syms(s))