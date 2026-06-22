from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from eth_utils import keccak
from web3 import Web3

from ..config import settings


class ChainVerificationError(Exception):
    pass


@dataclass(frozen=True)
class VerifiedReceipt:
    block_number: int


def _hex(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, int):
        return hex(value)
    if hasattr(value, "hex"):
        result = value.hex()
        return (result if result.startswith("0x") else f"0x{result}").lower()
    raise ChainVerificationError("invalid RPC hex value")


def _address(value: Any) -> str:
    if not value:
        return ""
    return str(value).lower()


def _topic_address(value: Any) -> str:
    raw = _hex(value).removeprefix("0x")
    return f"0x{raw[-40:]}".lower()


def _topic_int(value: Any) -> int:
    return int(_hex(value), 16)


def _int(value: Any) -> int:
    if isinstance(value, int):
        return value
    return int(_hex(value), 16)


def _event_topic(signature: str) -> str:
    return f"0x{keccak(text=signature).hex()}"


class ChainVerifier:
    def __init__(self, web3: Web3):
        self.web3 = web3

    def verify_proof_submission(
        self,
        *,
        tx_hash: str,
        address: str,
        chain_id: int,
        contract_address: str,
        day_index: int,
        proof_hash: str,
        approval_id: str,
    ) -> VerifiedReceipt:
        expected_contract = settings.proof_registry_address.lower()
        transaction, receipt = self._verify_transaction(
            tx_hash=tx_hash,
            address=address,
            chain_id=chain_id,
            submitted_contract=contract_address,
            expected_contract=expected_contract,
        )
        del transaction
        topic0 = _event_topic("ProofSubmitted(address,uint16,bytes32,bytes32)")
        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if (
                _address(log.get("address")) == expected_contract
                and len(topics) >= 4
                and _hex(topics[0]) == topic0
                and _topic_address(topics[1]) == address
                and _topic_int(topics[2]) == day_index
                and _hex(topics[3]) == approval_id.lower()
                and _hex(log.get("data")) == proof_hash.lower()
            ):
                return VerifiedReceipt(
                    block_number=_int(receipt.get("blockNumber", 0))
                )
        raise ChainVerificationError("expected ProofSubmitted event not found")

    def verify_day_mint(
        self,
        *,
        tx_hash: str,
        address: str,
        chain_id: int,
        contract_address: str,
        day_index: int,
    ) -> VerifiedReceipt:
        expected_contract = settings.restart_badge_address.lower()
        _, receipt = self._verify_transaction(
            tx_hash=tx_hash,
            address=address,
            chain_id=chain_id,
            submitted_contract=contract_address,
            expected_contract=expected_contract,
        )
        expected_token_id = int.from_bytes(
            keccak(bytes.fromhex(address[2:]) + bytes([day_index])),
            "big",
        )
        topic0 = _event_topic("DayMinted(address,uint8,uint256)")
        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if (
                _address(log.get("address")) == expected_contract
                and len(topics) >= 3
                and _hex(topics[0]) == topic0
                and _topic_address(topics[1]) == address
                and _topic_int(topics[2]) == day_index
                and int(_hex(log.get("data")), 16) == expected_token_id
            ):
                return VerifiedReceipt(
                    block_number=_int(receipt.get("blockNumber", 0))
                )
        raise ChainVerificationError("expected DayMinted event not found")

    def verify_final_mint(
        self,
        *,
        tx_hash: str,
        address: str,
        chain_id: int,
        contract_address: str,
    ) -> VerifiedReceipt:
        expected_contract = settings.restart_badge_address.lower()
        _, receipt = self._verify_transaction(
            tx_hash=tx_hash,
            address=address,
            chain_id=chain_id,
            submitted_contract=contract_address,
            expected_contract=expected_contract,
        )
        expected_token_id = int.from_bytes(
            keccak(bytes.fromhex(address[2:]) + bytes([99])),
            "big",
        )
        topic0 = _event_topic("FinalMinted(address,uint256)")
        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if (
                _address(log.get("address")) == expected_contract
                and len(topics) >= 2
                and _hex(topics[0]) == topic0
                and _topic_address(topics[1]) == address
                and int(_hex(log.get("data")), 16) == expected_token_id
            ):
                return VerifiedReceipt(
                    block_number=_int(receipt.get("blockNumber", 0))
                )
        raise ChainVerificationError("expected FinalMinted event not found")

    def verify_milestone_mint(
        self,
        *,
        tx_hash: str,
        address: str,
        chain_id: int,
        contract_address: str,
        token_id: int,
    ) -> VerifiedReceipt:
        expected_contract = settings.milestone_nft_address.lower()
        _, receipt = self._verify_transaction(
            tx_hash=tx_hash,
            address=address,
            chain_id=chain_id,
            submitted_contract=contract_address,
            expected_contract=expected_contract,
        )
        topic0 = _event_topic("Transfer(address,address,uint256)")
        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if (
                _address(log.get("address")) == expected_contract
                and len(topics) >= 4
                and _hex(topics[0]) == topic0
                and _topic_int(topics[1]) == 0
                and _topic_address(topics[2]) == address
                and _topic_int(topics[3]) == token_id
            ):
                return VerifiedReceipt(
                    block_number=_int(receipt.get("blockNumber", 0))
                )
        raise ChainVerificationError("expected milestone Transfer event not found")

    def _verify_transaction(
        self,
        *,
        tx_hash: str,
        address: str,
        chain_id: int,
        submitted_contract: str,
        expected_contract: str,
    ) -> tuple[Any, Any]:
        if expected_contract == "0x0000000000000000000000000000000000000000":
            raise ChainVerificationError("expected contract is not configured")
        if chain_id != settings.chain_id:
            raise ChainVerificationError("unexpected chain id")
        if submitted_contract.lower() != expected_contract:
            raise ChainVerificationError("unexpected contract address")
        if not settings.rpc_url:
            raise ChainVerificationError("RPC_URL is not configured")
        try:
            rpc_chain_id = int(self.web3.eth.chain_id)
            transaction = self.web3.eth.get_transaction(tx_hash)
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        except Exception as exc:
            raise ChainVerificationError("transaction receipt is unavailable") from exc
        if rpc_chain_id != settings.chain_id:
            raise ChainVerificationError("RPC is connected to the wrong chain")
        if _int(receipt.get("status", 0)) != 1:
            raise ChainVerificationError("transaction reverted")
        if _address(transaction.get("from")) != address:
            raise ChainVerificationError("transaction sender does not match address")
        if _address(transaction.get("to")) != expected_contract:
            raise ChainVerificationError("transaction target does not match contract")
        return transaction, receipt


def get_chain_verifier() -> ChainVerifier:
    return ChainVerifier(Web3(Web3.HTTPProvider(settings.rpc_url)))
