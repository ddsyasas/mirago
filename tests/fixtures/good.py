"""Example file with all real imports. mirago should report nothing."""

import os
import sys
from pathlib import Path
from typing import Optional

import requests


def main() -> None:
    path = Path(".")
    response = requests.get("https://example.com")
    print(os.getcwd(), sys.version, path, response.status_code)
