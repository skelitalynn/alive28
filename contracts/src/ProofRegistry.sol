// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

contract ProofRegistry {
    using MessageHashUtils for bytes32;

    address public immutable validator;
    mapping(address => mapping(uint16 => bytes32)) private proofs;
    mapping(bytes32 => bool) public usedApprovals;

    event ProofSubmitted(
        address indexed user,
        uint16 indexed dayIndex,
        bytes32 proofHash,
        bytes32 indexed approvalId
    );

    constructor(address validator_) {
        require(validator_ != address(0), "invalid validator");
        validator = validator_;
    }

    function approvalDigest(
        address user,
        uint16 dayIndex,
        bytes32 proofHash,
        uint64 deadline,
        bytes32 approvalId
    ) public view returns (bytes32) {
        bytes32 payloadHash = keccak256(
            abi.encode(
                address(this),
                block.chainid,
                user,
                dayIndex,
                proofHash,
                deadline,
                approvalId
            )
        );
        return payloadHash.toEthSignedMessageHash();
    }

    function submitProof(
        uint16 dayIndex,
        bytes32 proofHash,
        uint64 deadline,
        bytes32 approvalId,
        bytes calldata signature
    ) external {
        require(dayIndex >= 1 && dayIndex <= 28, "invalid dayIndex");
        require(block.timestamp <= deadline, "approval expired");
        require(!usedApprovals[approvalId], "approval already used");
        require(proofs[msg.sender][dayIndex] == bytes32(0), "already submitted");

        address recovered = ECDSA.recover(
            approvalDigest(
                msg.sender,
                dayIndex,
                proofHash,
                deadline,
                approvalId
            ),
            signature
        );
        require(recovered == validator, "invalid approval");

        usedApprovals[approvalId] = true;
        proofs[msg.sender][dayIndex] = proofHash;
        emit ProofSubmitted(msg.sender, dayIndex, proofHash, approvalId);
    }

    function getProof(address user, uint16 dayIndex) external view returns (bytes32) {
        return proofs[user][dayIndex];
    }
}
