from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

from eth_account import Account
from eth_account.messages import encode_defunct
from sqlmodel import Session, select

from ..config import settings
from ..models import WalletChallenge, WalletSession


class AuthenticationError(Exception):
    pass


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_wallet_challenge(
    session: Session,
    address: str,
) -> WalletChallenge:
    now = datetime.utcnow()
    nonce = secrets.token_hex(16)
    expires_at = now + timedelta(seconds=settings.auth_nonce_ttl_seconds)
    message = "\n".join(
        [
            "Alive28 wallet authentication",
            f"Address: {address}",
            f"Chain ID: {settings.chain_id}",
            f"Nonce: {nonce}",
            f"Issued At: {now.isoformat()}Z",
            f"Expiration Time: {expires_at.isoformat()}Z",
            "This request will not trigger a blockchain transaction.",
        ]
    )
    challenge = WalletChallenge(
        id=str(uuid.uuid4()),
        address=address,
        nonce=nonce,
        message=message,
        expires_at=expires_at,
    )
    session.add(challenge)
    session.commit()
    session.refresh(challenge)
    return challenge


def verify_wallet_signature(
    session: Session,
    address: str,
    signature: str,
) -> tuple[str, WalletSession]:
    now = datetime.utcnow()
    challenge = session.exec(
        select(WalletChallenge)
        .where(
            WalletChallenge.address == address,
            WalletChallenge.used_at.is_(None),
        )
        .order_by(WalletChallenge.created_at.desc())
    ).first()
    if not challenge or challenge.expires_at <= now:
        raise AuthenticationError("challenge is missing, expired, or already used")

    try:
        recovered = Account.recover_message(
            encode_defunct(text=challenge.message),
            signature=signature,
        ).lower()
    except Exception as exc:
        raise AuthenticationError("invalid wallet signature") from exc
    if recovered != address:
        raise AuthenticationError("signature does not match address")

    token = secrets.token_urlsafe(32)
    wallet_session = WalletSession(
        id=str(uuid.uuid4()),
        address=address,
        token_hash=_token_hash(token),
        expires_at=now + timedelta(seconds=settings.auth_session_ttl_seconds),
    )
    challenge.used_at = now
    session.add(challenge)
    session.add(wallet_session)
    session.commit()
    session.refresh(wallet_session)
    return token, wallet_session


def authenticate_bearer_token(
    session: Session,
    authorization: str | None,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("wallet session required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("wallet session required")

    now = datetime.utcnow()
    wallet_session = session.exec(
        select(WalletSession).where(
            WalletSession.token_hash == _token_hash(token),
            WalletSession.revoked_at.is_(None),
        )
    ).first()
    if not wallet_session or wallet_session.expires_at <= now:
        raise AuthenticationError("wallet session is invalid or expired")
    return wallet_session.address
