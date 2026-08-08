from pathlib import Path

import pytest

from omni.errors import ConversionError
from omni.texconv import TEXT_ENCODINGS, convert_base64, convert_hex, convert_text


def test_encodings_defined():
    assert set(TEXT_ENCODINGS) == {"utf-8", "utf-16", "utf-16-le", "utf-16-be", "ascii", "latin-1"}


def test_utf8_to_utf16_roundtrip(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("Hello ünïcode", encoding="utf-8")
    dst = tmp_path / "a16.txt"
    convert_text(src, dst, in_enc="utf-8", out_enc="utf-16")
    back = tmp_path / "back.txt"
    convert_text(dst, back, in_enc="utf-16", out_enc="utf-8")
    assert back.read_text(encoding="utf-8") == "Hello ünïcode"


def test_bad_bytes_raise(tmp_path):
    src = tmp_path / "bad.txt"
    src.write_bytes(b"\xff\xfe\x00 invalid")
    with pytest.raises(ConversionError):
        convert_text(src, tmp_path / "x.txt", in_enc="ascii", out_enc="utf-8")


def test_newline_normalization(tmp_path):
    src = tmp_path / "crlf.txt"
    src.write_bytes(b"a\r\nb\rc")
    dst = tmp_path / "lf.txt"
    convert_text(src, dst, out_enc="utf-8", newline="\n")
    assert dst.read_text(encoding="utf-8") == "a\nb\nc"


def test_base64_encode_decode_files(tmp_path):
    src = tmp_path / "raw.bin"
    src.write_bytes(b"\x00\x01hello")
    enc = tmp_path / "enc.txt"
    convert_base64(src, enc, "encode")
    assert enc.read_text(encoding="utf-8") == "AAFoZWxsbw=="
    dec = tmp_path / "dec.bin"
    convert_base64(enc, dec, "decode")
    assert dec.read_bytes() == b"\x00\x01hello"


def test_hex_encode_decode_files(tmp_path):
    src = tmp_path / "raw.bin"
    src.write_bytes(b"\x00\xffAB")
    enc = tmp_path / "hex.txt"
    convert_hex(src, enc, "encode")
    assert enc.read_text(encoding="utf-8") == "00ff4142"
    dec = tmp_path / "dec.bin"
    convert_hex(enc, dec, "decode")
    assert dec.read_bytes() == b"\x00\xffAB"


def test_missing_source_raises(tmp_path):
    with pytest.raises(ConversionError):
        convert_text(tmp_path / "nope.txt", tmp_path / "x.txt")