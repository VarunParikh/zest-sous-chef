"""`make data` also runs mock-data/check_seed.py and check_taxonomy.py. Block 3.3 found check_seed's own taxonomy parser
had not learned the C68 `!term` marker, so `make data` failed while V1 to V17 passed. These run both scripts as make does."""
import subprocess
import sys

import pytest


@pytest.mark.parametrize("script", ["mock-data/check_seed.py", "mock-data/check_taxonomy.py"])
def test_seed_check_script_exits_zero(script):
    r = subprocess.run([sys.executable, script], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
