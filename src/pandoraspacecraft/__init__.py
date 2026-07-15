# Standard library
import os  # noqa

from astropy.config import get_cache_dir

PACKAGEDIR = os.path.abspath(os.path.dirname(__file__))
CACHEDIR = get_cache_dir("pandoraspacecraft") + "/download/url/"
TEST_MODE = False


def enable_test_mode():
    global TEST_MODE
    TEST_MODE = True


def disable_test_mode():
    global TEST_MODE
    TEST_MODE = False


def is_test_mode():
    return TEST_MODE


from importlib.metadata import PackageNotFoundError, version  # noqa


def get_version():
    try:
        return version("pandoraspacecraft")
    except PackageNotFoundError:
        return "unknown"


__version__ = get_version()

import logging  # noqa: E402
import os  # noqa
from glob import glob  # noqa
from pathlib import Path  # noqa

log = logging.getLogger("pandoraspacecraft")

# PACKAGEDIR = os.path.abspath(os.path.dirname(__file__))
# KERNELDIR = f"{PACKAGEDIR}/data/kernels/"
# TLEDIR = f"{PACKAGEDIR}/data/tle/"


PACKAGEDIR = str(Path(__file__).resolve().parent)
PROJECTDIR = str(Path(__file__).resolve().parents[2])
KERNELDIR = str(Path(PACKAGEDIR) / "data" / "kernels") + os.sep
TLEDIR = str(Path(PACKAGEDIR) / "data" / "tle") + os.sep

from .spacecraft import PandoraSpacecraft  # noqa
