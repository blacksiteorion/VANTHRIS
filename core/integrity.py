import hashlib
import os
from utils.logger import log


def calculate_sha256(filepath, chunk_size=65536):
    """Calculate the SHA-256 hash of a file without loading it all into memory."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (FileNotFoundError, PermissionError) as e:
        log.error(f"[bold red]Hash failed for {filepath}:[/] {e}")
        return None
