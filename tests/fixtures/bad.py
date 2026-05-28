"""Example file with hallucinated imports. mirago should flag the fakes."""

import os                                            # real (stdlib)
import fastjson_validator                            # hallucinated
from requests import get                             # real
from notarealmodule_xyz_mirago import something      # hallucinated
import pandas                                        # real
from json_super_fast_2026 import parse               # hallucinated
