import base64
import hashlib
import zlib
from pathlib import Path

from omni.errors import ConversionError

HASH_ALGORITHMS = ("md5", "sha1", "sha224", "sha256", "sha384", "sha512", "sha3_256", "sha3_512", "blake2b")


def hash_bytes(data: bytes) -> dict[str, str]:
    out = {algo: hashlib.new(algo, data).hexdigest() for algo in HASH_ALGORITHMS}
    out["crc32"] = format(zlib.crc32(data) & 0xFFFFFFFF, "08x")
    return out


def hash_text(text: str) -> dict[str, str]:
    return hash_bytes(text.encode("utf-8"))


def hash_file(path: str | Path) -> dict[str, str]:
    digests = {algo: hashlib.new(algo) for algo in HASH_ALGORITHMS}
    crc = 0
    with open(path, "rb") as fh:
        while chunk := fh.read(65536):
            for d in digests.values():
                d.update(chunk)
            crc = zlib.crc32(chunk, crc)
    out = {algo: d.hexdigest() for algo, d in digests.items()}
    out["crc32"] = format(crc & 0xFFFFFFFF, "08x")
    return out


def encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decode_base64(s: str) -> bytes:
    try:
        return base64.b64decode(s.strip(), validate=True)
    except Exception as exc:
        raise ConversionError("Invalid Base64 input") from exc


def to_hex(data: bytes) -> str:
    return data.hex()


def from_hex(s: str) -> bytes:
    try:
        return bytes.fromhex("".join(s.strip().split()))
    except ValueError as exc:
        raise ConversionError("Invalid hexadecimal input") from exc