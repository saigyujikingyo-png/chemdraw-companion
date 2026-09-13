"""Read a separately bound local calibration; never trust scene tolerances.

This prototype checks content/asset/style/build consistency. Neither a native
build string nor measurement_source authenticates a real ChemDraw execution.
Its tests and synthetic measurements are not native scientific evidence. This
module does not modify or repair the existing c92a918 runtime/probe call sites.

The returned conservative_forward_extension_pt describes measured head extent;
it must NEVER be added to a policy's tip/target or tail/source acceptance limit.
The oracle measures the visible tip from a bound mask. uncertainty_pt makes
acceptance more conservative, not more permissive.
"""
import json
import math
from common import asset_bytes, require, validate_schema

NUMERIC_STYLE_FIELDS = ("font_pt", "bond_pt", "stroke_pt", "head_size",
                        "head_width", "head_center_size")
STRING_STYLE_FIELDS = ("font_family", "head_type", "head", "tail", "curve_type")
STYLE_FIELDS = frozenset(NUMERIC_STYLE_FIELDS + STRING_STYLE_FIELDS)


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _style(value, label):
    require(isinstance(value, dict) and set(value) == STYLE_FIELDS,
            "calibration " + label + " must contain exactly the complete style fields")
    for key in NUMERIC_STYLE_FIELDS:
        require(_finite_number(value[key]) and value[key] > 0,
                "calibration " + label + " nonfinite/nonpositive style: " + key)
    for key in STRING_STYLE_FIELDS:
        require(isinstance(value[key], str) and bool(value[key].strip()),
                "calibration " + label + " empty/nonstring style: " + key)


def _unique_members(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "calibration duplicate JSON key: " + key)
        result[key] = value
    return result


def _non_json_number(value):
    raise ValueError("calibration nonfinite JSON number: " + value)


def load_calibration(asset, base_dir, expected_style, expected_native_build):
    """Return verified calibration fields and a derived bounded head extent.

    asset is {id, path, bytes, sha256, kind='calibration'}. Asset descriptor trust
    belongs to the independent oracle request, never to a mutable scene. The
    common reader confines paths to base_dir and verifies exact bytes/hash; the
    same verified bytes are parsed, avoiding a second file read after hashing.
    All eleven style fields and the build string must match the independently
    supplied expectations. This v1 measured family is restricted to a total
    forward extent (measurement plus uncertainty) no larger than one bond.
    """
    require(isinstance(asset, dict) and asset.get("kind") == "calibration",
            "missing or invalid calibration asset")
    require(isinstance(asset.get("id"), str) and bool(asset["id"].strip()),
            "calibration asset identity missing")
    _style(expected_style, "expected")
    require(isinstance(expected_native_build, str) and bool(expected_native_build.strip()),
            "calibration expected native build missing")
    try:
        data = asset_bytes(asset, base_dir)
    except OSError as exc:
        raise ValueError("calibration asset unavailable") from exc
    try:
        value = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_unique_members,
                           parse_constant=_non_json_number)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("calibration invalid UTF-8 JSON") from exc
    validate_schema("calibration.schema.json", value)
    _style(value["style"], "measured")
    require(value["style"] == expected_style, "calibration style mismatch")
    require(value["native_build"] == expected_native_build, "calibration native build mismatch")
    require(value["measurement_status"] == "measured", "calibration measurement is unavailable or uncertain")
    limits = value["limits"]
    for key in ("head_extension_pt", "uncertainty_pt"):
        require(_finite_number(limits[key]) and limits[key] >= 0,
                "calibration nonfinite/negative limit: " + key)
    conservative = limits["head_extension_pt"] + limits["uncertainty_pt"]
    require(_finite_number(conservative) and conservative <= value["style"]["bond_pt"],
            "calibration measured extent plus uncertainty exceeds one bond")
    return {**value, "asset_id": asset["id"], "asset_sha256": asset["sha256"],
            "conservative_forward_extension_pt": conservative}
