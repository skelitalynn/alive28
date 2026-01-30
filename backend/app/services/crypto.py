import hashlib
import secrets
from eth_utils import keccak


def normalize_text(text: str, max_len: int = 500) -> str:
    if text is None:
        return ""
    cleaned = " ".join(text.strip().split())
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_salt_hex(num_bytes: int = 16) -> str:
    return "0x" + secrets.token_hex(num_bytes)


def compute_proof_hash(date_key: str, normalized_text: str, salt_hex: str) -> str:
    payload = f"{date_key}|{normalized_text}|{salt_hex}"
    digest = keccak(text=payload)
    return "0x" + digest.hex()
