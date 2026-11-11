"""Fixed shapes that exercise a fit, the token limit and lexer errors."""

from pathlib import Path


def focused(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    prefix = b"[\n" + b"0," * 95_000 + b"\n"
    payload = ('é😀\\n\\uD83D\\uDE00' * 3800).encode("utf-8")
    cases = {
        "probe-fits.json": prefix + b'"' + payload + b'"\n]\n',
        "probe-limit.json": b"[" + b"0," * 134_999 + b"0]",
        "probe-invalid-number.json": prefix + b'"' + payload + b'",\n1e+\n]',
        "probe-invalid-utf8.json": prefix + b'"' + payload + b'\xff"\n]',
    }
    for name, data in cases.items():
        (directory / name).write_bytes(data)
    return [directory / name for name in cases]
