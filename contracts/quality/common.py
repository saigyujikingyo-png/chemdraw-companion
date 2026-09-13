"""Shared local evidence checks; no network, native execution or approval authority."""
import hashlib
import json
import math
from pathlib import Path
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent

def require(condition, message):
    if not condition:
        raise ValueError(message)

def finite(value):
    if isinstance(value, float):
        require(math.isfinite(value), "nonfinite JSON number")
    elif isinstance(value, dict):
        for item in value.values(): finite(item)
    elif isinstance(value, list):
        for item in value: finite(item)

def parse_json_bytes(data):
    def members(pairs):
        result = {}
        for key,value in pairs:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    value = json.loads(data.decode("utf-8-sig"), object_pairs_hook=members)
    finite(value)
    return value

def read_json(path):
    value = parse_json_bytes(Path(path).read_bytes())
    finite(value)
    return value

def validate_schema(filename, value):
    finite(value)
    schema = read_json(HERE / filename)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value),
                    key=lambda e: str(list(e.path)))
    require(not errors, str(list(errors[0].path)) + ": " + errors[0].message if errors else "")

def asset_bytes(asset, base_dir):
    base = Path(base_dir).resolve()
    relative = Path(asset["path"])
    require(not relative.is_absolute(), "absolute asset path")
    path = (base / relative).resolve()
    require(path.is_relative_to(base), "asset path escapes bundle")
    data = path.read_bytes()
    require(type(asset["bytes"]) is int and len(data) == asset["bytes"], "asset byte count mismatch")
    require(hashlib.sha256(data).hexdigest() == asset["sha256"], "asset SHA-256 mismatch")
    return data
