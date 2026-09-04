#!/usr/bin/env python3
"""tests/test_decode.py — unit tests for binary decoder."""
import sys, pathlib, importlib.util, pytest

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location("arg_fetch", ROOT / "arg_fetch.py")
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {ROOT / 'arg_fetch.py'}")
arg_fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arg_fetch)


def test_decode_binary_known():
    """The exact binary from the discovered transmission."""
    binary = (
        "00111110 00111110 01010010 01110101 01101110 00100000 01110011 \n"
        "01111001 01110011 01110100 01100101 01101101 01110011 00100000 \n"
        "01100011 01101000 01100101 01100011 01101011 00101110 00100000"
    )
    expected = ">>Run systems check. "
    assert arg_fetch.decode_binary(binary) == expected


def test_decode_binary_with_whitespace():
    binary = "00100000\n00100000\n00111110"
    # split() collapses whitespace; newlines aren't preserved.
    # 00100000 = 0x20 = ' ', 00111110 = 0x3E = '>'
    assert arg_fetch.decode_binary(binary) == "  >"


def test_decode_binary_filters_invalid():
    """Non-8-bit chunks are filtered out; invalid bits become '?'."""
    binary = "00111110 0 01110101 00111111 12345"
    result = arg_fetch.decode_binary(binary)
    assert result == ">u?"


def test_decode_binary_empty():
    assert arg_fetch.decode_binary("") == ""
    assert arg_fetch.decode_binary("   \n  ") == ""


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))