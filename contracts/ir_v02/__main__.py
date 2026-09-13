"""Typed, non-overwriting command line for the coordinate-free contract."""
import argparse
import json
import sys
from pathlib import Path
from . import IRContractError, migrate_v01, validate_mechanism, compile_electron_flows, lower_depiction


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise IRContractError("CLI_ARGUMENT_ERROR", "$", message)


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise IRContractError("INPUT_READ_ERROR", str(path), "Could not read valid JSON input", {"reason": str(exc)}) from exc


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("operation", choices=["validate", "migrate", "compile", "lower"])
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--policy", choices=["strict", "preserve_v01_display"], default="strict")
    parser.add_argument("--depiction")
    args, status, result = None, 0, None
    try:
        args = parser.parse_args(argv)
        output = Path(args.output)
        if output.exists() or output.resolve() == Path(args.input).resolve():
            raise IRContractError("OUTPUT_EXISTS", str(output), "A new output path is required; input and existing files are never overwritten")
        ir = _read(args.input)
        if args.operation == "migrate":
            result = migrate_v01(ir, policy=args.policy, depiction_states=_read(args.depiction) if args.depiction else None)
        else:
            if args.depiction or args.policy != "strict":
                raise IRContractError("CLI_ARGUMENT_ERROR", "$", "Migration options are only valid for migrate")
            result = {"validate": validate_mechanism, "compile": compile_electron_flows, "lower": lower_depiction}[args.operation](ir)
    except IRContractError as exc:
        status, result = 1, {"status": "failed", "error": exc.to_dict()}
    except Exception as exc:
        status, result = 1, {"status": "failed", "error": {"code": "INTERNAL_CONTRACT_ERROR", "path": "$", "message": str(exc), "details": {"exception_type": type(exc).__name__}}}
    if args is not None:
        output = Path(args.output)
        try:
            with output.open("x", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2, ensure_ascii=False, allow_nan=False)
                handle.write("\n")
        except OSError as exc:
            if not (isinstance(exc, FileExistsError) and status):
                status, result = 1, {"status": "failed", "error": {"code": "OUTPUT_WRITE_ERROR", "path": str(output), "message": str(exc), "details": {}}}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
