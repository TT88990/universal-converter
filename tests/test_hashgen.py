import tempfile
from pathlib import Path

import pytest

from omni.errors import ConversionError
from omni.hashgen import (
    decode_base64,
    encode_base64,
    from_hex,
    hash_bytes,
    hash_file,
    hash_text,
    to_hex,
)


def test_md5_known_vector():
    assert hash_text("abc")["md5"] == "900150983cd24fb0d6963f7d28e17f72"


def test_sha256_known_vector():
    assert hash_text("abc")["sha256"] == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_crc32_vector():
    assert hash_text("hello")["crc32"] == "3610a686"


def test_all_algos_present():
    h = hash_text("abc")
    for algo in ("md5", "sha1", "sha224", "sha256", "sha384", "sha512", "sha3_256", "sha3_512", "blake2b", "crc32"):
        assert algo in h and len(h[algo]) > 0


def test_hash_bytes_and_text_agree():
    assert hash_bytes(b"abc")["md5"] == hash_text("abc")["md5"]


def test_file_hash_matches_text(tmp_path):
    p = tmp_path / "fixture.txt"
    p.write_text("abc", encoding="utf-8")
    assert hash_file(p)["md5"] == hash_text("abc")["md5"]


def test_base64_roundtrip():
    assert encode_base64(b"hello world") == "aGVsbG8gd29ybGQ="
    assert decode_base64("aGVsbG8gd29ybGQ=") == b"hello world"


def test_base64_decode_invalid():
    with pytest.raises(ConversionError):
        decode_base64("!!not-base64!!")


def test_hex_roundtrip_and_errors():
    assert to_hex(b"\x00\xff") == "00ff"
    assert from_hex("00 ff") == b"\x00\xff"
    with pytest.raises(ConversionError):
        from_hex("zz")