# flake8: noqa
import os
import shutil
import subprocess
import tempfile
import warnings
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy.utils.data import CacheMissingWarning, cache_contents
from astropy.utils.data import clear_download_cache as _astropy_clear_download_cache
from astropy.utils.data import download_file, import_file_to_cache, is_url_in_cache
from tqdm import tqdm

from . import CACHEDIR, KERNELDIR, PACKAGEDIR, TLEDIR, log

META_START = """KPL/MK

pandoraspacecraft meta kernel
==============

The generic kernels listed below can be obtained from NAIF generic kernels:
    https://naif.jpl.nasa.gov/pub/naif/generic_kernels/

\\begindata

"""
META_END = """

\\begintext   
"""


PANDORADIRECTIONS = {
    "boresight": np.asarray([0, 0, 1]),
    "st1": np.asarray([0.6804, -0.7071, -0.1923]),
    "st2": np.asarray([0.6804, 0.7071, -0.1923]),
    "x": np.asarray([1, 0, 0]),
    "y": np.asarray([0, 1, 0]),
    "z": np.asarray([0, 0, 1]),
    "-x": np.asarray([-1, 0, 0]),
    "-y": np.asarray([0, -1, 0]),
    "-z": np.asarray([0, 0, -1]),
    "cmddir9": np.asarray(
        [-0.0004612914234377, 0.0002760008782731, 0.9999998555168587]
    ),
    "cmddir10": np.asarray([-0.00062173651702, -0.00108778168473, 0.999999215087047]),
}


def clear_cache(all=False):
    if all:
        _astropy_clear_download_cache(pkgname="pandoraspacecraft")
    else:
        toclear = [
            key
            for key in cache_contents("pandoraspacecraft").keys()
            if key.split("/")[-1].startswith("pandora")
            and (key.endswith("bsp") | key.endswith("bc"))
        ]
        [
            _astropy_clear_download_cache(url, pkgname="pandoraspacecraft")
            for url in toclear
        ]


def truncate_directory_string(directory, max_length=50):
    """Turns a directory string into a SPICE compliant list of directories...

    SPICE limits every string in a text kernel to 80 characters, so a long
    directory is broken into several strings, each continued with a trailing
    "+". The pieces are split on component boundaries using `Path.parts`, so
    this works with both POSIX roots ("/") and Windows drives ("C:\\").
    """
    parts = Path(directory).parts
    if not parts:
        return [""]

    # `parts[0]` is the anchor -- "/" on POSIX, "C:\\" on Windows -- and already
    # ends in a separator, so the first component is appended without one.
    lines = []
    line = parts[0]
    for part in parts[1:]:
        if len(line) < max_length:
            line = line + part if line.endswith(os.sep) else line + os.sep + part
        else:
            lines.append(line + "+")
            line = os.sep + part
    lines.append(line)
    return lines


def kernel_entry(symbol, relative_path):
    """Build one KERNELS_TO_LOAD entry, e.g. "$cache/<hash>/contents".

    SPICE pastes the PATH_VALUE for `symbol` onto whatever follows it, so the
    separator here has to match the one in PATH_VALUES. SPICE accepts either
    separator on Windows, but keeping them consistent keeps the meta kernel
    readable.
    """
    return f"${symbol}{os.sep}{relative_path}"


def create_meta_kernel(tles_only=False):
    """Create a meta kernel out of the cached SPICE kernels"""
    KERNELS = {
        "naif0012.tls": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/",
        "de440.bsp": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/",
        "pck00011.tpc": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/",
        "earth_latest_high_prec.bpc": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/",
    }
    if not tles_only:
        ndays = 190
        for idx in np.arange(0, ndays + 1, 1):
            t = (Time.strptime("2026011", format_string="%Y%j") + idx * u.day).strftime(
                "%Y%j"
            )
            KERNELS[f"pandora_{t}.bc"] = (
                "https://github.com/PandoraMission/pandora-spacecraft/raw/main/src/pandoraspacecraft/data/kernels/Pandora/"
            )
            KERNELS[f"pandora_{t}.bsp"] = (
                "https://github.com/PandoraMission/pandora-spacecraft/raw/main/src/pandoraspacecraft/data/kernels/Pandora/"
            )

    paths = get_file_paths(KERNELS)
    if not tles_only:
        cached = [
            Path(value)
            for item, value in cache_contents(pkgname="pandoraspacecraft").items()
            if item.split("/")[-1].startswith("pandora") & (item.endswith(".spk"))
            | item.endswith(".bc")
            | item.endswith(".bsp")
        ]
        paths = paths + sorted(path for path in cached if path not in paths)
    if len(paths) == 0:
        raise ValueError(
            "Can not find any SPICE kernels. Check documentation on installation."
        )
    cache_dirs = {path.parent.parent for path in paths}
    if len(cache_dirs) != 1:
        raise ValueError(
            "You have provided multiple cache directories for SPICE kernels, try reinstalling."
        )
    cache_dir = cache_dirs.pop()

    path_values = []
    path_symbols = []
    kernels_to_load = []

    for dirname in sorted(KERNELDIR.iterdir()):
        if dirname.name == "testkernels":
            continue
        path_values.extend(truncate_directory_string(dirname))
        path_symbols.append(dirname.name)
        for d in sorted(dirname.iterdir()):
            if (not d.name.endswith("bsp")) and (not d.name.endswith("bc")):
                kernels_to_load.append(_kernel_entry(dirname.name, d.name))
            elif d.name == "pandora_tle.bsp":
                kernels_to_load.append(_kernel_entry(dirname.name, "pandora_tle.bsp"))
    path_values.extend(truncate_directory_string(cache_dir))
    path_symbols.extend(["cache"])
    kernels_to_load.extend(
        [_kernel_entry("cache", path.relative_to(cache_dir)) for path in paths]
    )

    def format_list(l, pad=10):
        if len(l) == 0:
            return ""
        if len(l) == 1:
            return f" '{l[0]}'"
        output = f" '{l[0]}'"
        for i in l[1:]:
            output += "\n" + "".join([" "] * pad) + "'" + i + "'"
        return output

    output = f"""{META_START}
    \n    PATH_VALUES = ({format_list(path_values, 20)}              )
    \n    PATH_SYMBOLS = ({format_list(path_symbols, 21)}              )
    \n    KERNELS_TO_LOAD = ({format_list(kernels_to_load, 24)}              )
    {META_END}
    """

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(output)
        # Get the file name
        temp_file_name = temp_file.name

    import_file_to_cache(
        "https://github.com/pandoramission/pandoraspacecraft/src/pandoraspacecraft/data/Meta.txt",
        temp_file_name,
        pkgname="pandoraspacecraft",
    )
    return


def get_file_path(url):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", CacheMissingWarning)
        return Path(
            download_file(
                url, cache=True, show_progress=False, pkgname="pandoraspacecraft"
            )
        )


def get_file_paths(file_dictionary):
    """Ensure the file is downloaded and valid using Astropy's download_file."""
    file_paths = []
    file_names = list(file_dictionary.keys())
    progress_bar = None
    for idx, file_name in enumerate(file_names):
        log.debug(f"Finding {file_name}.")
        url = file_dictionary[file_name]
        if is_url_in_cache(url + file_name, pkgname="pandoraspacecraft"):
            file_paths.append(get_file_path(url + file_name))
            log.debug(f"Found {file_name} in cache.")
        else:
            if progress_bar is None:
                progress_bar = tqdm(
                    range(0, len(file_names)),
                    initial=idx,
                    total=len(file_names),
                    desc="Downloading SPICE Kernels",
                )
            file_paths.append(get_file_path(url + file_name))
            progress_bar.n = idx
            progress_bar.refresh()
            log.debug(f"Downloaded {file_name}.")
    return file_paths


def vec_to_radec(x, y, z):
    r = np.sqrt(x * x + y * y + z * z)
    ra = np.arctan2(y, x)  # [-pi, pi]
    ra = ra % (2 * np.pi)  # [0, 2pi)
    dec = np.arcsin(z / r)
    return np.degrees(ra), np.degrees(dec)


def vec_to_coord(x, y, z):
    ra, dec = vec_to_radec(x, y, z)
    return SkyCoord(ra, dec, unit="deg")


def radec_to_vec(ra, dec):
    ra, dec = u.Quantity(ra, "deg").to(u.rad), u.Quantity(dec, "deg").to(u.rad)
    ca, sa = np.cos(ra.value), np.sin(ra.value)
    cd, sd = np.cos(dec.value), np.sin(dec.value)
    return np.array([cd * ca, cd * sa, sd], dtype=float)


def radec_to_east(ra, dec):
    ra, dec = u.Quantity(ra, "deg").to(u.rad), u.Quantity(dec, "deg").to(u.rad)
    return np.array([-np.sin(ra.value), np.cos(ra.value), 0.0])


def radec_to_north(ra, dec):
    ra, dec = u.Quantity(ra, "deg").to(u.rad), u.Quantity(dec, "deg").to(u.rad)
    return np.array(
        [
            -np.sin(dec.value) * np.cos(ra.value),
            -np.sin(dec.value) * np.sin(ra.value),
            np.cos(dec.value),
        ]
    )


def radec_from_vec(v):
    x, y, z = v
    r = np.linalg.norm(v)
    ra = np.degrees(np.arctan2(y, x)) % 360.0
    dec = np.degrees(np.arcsin(z / r))
    return ra, dec


def coord_to_vec(coord):
    return radec_to_vec(coord.ra, coord.dec)


def rotmat_from_xyzw(quats):
    x, y, z, w = quats.T
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def get_pointing_vector_from_quats(quats, direction="boresight"):
    R = rotmat_from_xyzw(quats)
    pointing = np.dot(
        R.transpose([2, 0, 1]),
        PANDORADIRECTIONS[direction] if isinstance(direction, str) else direction,
    )
    pointing /= np.linalg.norm(pointing, axis=1)[:, None]
    return pointing


def quat_xyzw_to_radec(q, boresight=np.array([0.0, 0.0, 1.0])):
    R = rotmat_from_xyzw(q)
    v_inertial = R @ boresight
    return radec_from_vec(v_inertial)


def slerp(q0, q1, t, eps=1e-8):
    """
    SLERP between unit quaternions q0 and q1.
    q0, q1: shape (4,), scalar-last [x,y,z,w]
    t: float in [0,1]
    Returns unit quaternion, scalar-last.
    """

    def normalize(q):
        q = np.asarray(q, dtype=float)
        return q / np.linalg.norm(q)

    q0 = normalize(q0)
    q1 = normalize(q1)

    d = np.dot(q0, q1)

    # Same-rotation ambiguity fix (prevents 180° wrap issues)
    if d < 0.0:
        q1 = -q1
        d = -d

    # If very close, fall back to normalized lerp (avoids numeric issues)
    if d > 1.0 - eps:
        q = q0 + t * (q1 - q0)
        return normalize(q)

    theta = np.arccos(np.clip(d, -1.0, 1.0))
    sin_theta = np.sin(theta)

    w0 = np.sin((1.0 - t) * theta) / sin_theta
    w1 = np.sin(t * theta) / sin_theta
    return w0 * q0 + w1 * q1


def interp_quat(times, quats, t):
    times = np.asarray(times, dtype=float)
    quats = np.asarray(quats, dtype=float)

    i = np.searchsorted(times, t) - 1
    i = np.clip(i, 0, len(times) - 2)

    t0, t1 = times[i], times[i + 1]
    u = (t - t0) / (t1 - t0)
    return slerp(quats[i], quats[i + 1], u)


def angle_between(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    norm = (
        np.linalg.norm(np.atleast_1d(a), axis=1)[:, None]
        * np.linalg.norm(np.atleast_1d(b), axis=1)[:, None]
    )
    cos_theta = np.asarray(
        [
            np.dot(np.atleast_1d(a1), np.atleast_1d(b1)) / norm1
            for a1, b1, norm1 in zip(a, b, norm)
        ]
    )[:, 0]
    # numerical safety
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    if a.ndim == 0:
        return np.arccos(cos_theta[0])
    return np.arccos(cos_theta)  # radians


import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.time import Time
from astropy.utils.data import cache_contents

import pandoraspacecraft as ps
from pandoraspacecraft.maintenance import *


def find_merged_gaps(t, gap_threshold=100.0, merge_threshold=1000.0):
    """
    Return merged gap edges as index tuples (left_index, right_index).

    Each tuple corresponds to a gap spanning:
        t[left_index] -> t[right_index]
    """

    t = np.asarray(t, dtype=float)
    if t.ndim != 1:
        raise ValueError("t must be 1D")
    if len(t) < 2:
        return []
    if np.any(np.diff(t) < 0):
        raise ValueError("t must be sorted ascending")

    dt = np.diff(t)

    # indices i where gap is between t[i] and t[i+1]
    gap_idx = np.where(dt > gap_threshold)[0]
    if len(gap_idx) == 0:
        return []

    # initialize first gap
    cur_left = gap_idx[0]
    cur_right = gap_idx[0] + 1

    merged = []

    for i in gap_idx[1:]:
        left = i
        right = i + 1

        separation = t[left] - t[cur_right]

        if separation <= merge_threshold:
            # extend current merged gap
            cur_right = right
        else:
            merged.append((cur_left, cur_right))
            cur_left, cur_right = left, right

    merged.append((cur_left, cur_right))

    return merged


def import_from_packagedir_to_cache():
    for path in sorted((KERNELDIR / "Pandora").iterdir()):
        fname = path.name
        if not fname.startswith("pandora_2"):
            continue
        if (fname.endswith("bsp")) | (fname.endswith("bc")):
            import_file_to_cache(
                f"https://github.com/PandoraMission/pandora-spacecraft/raw/main/src/pandoraspacecraft/data/kernels/Pandora/{fname}",
                str(path),
                pkgname="pandoraspacecraft",
            )
