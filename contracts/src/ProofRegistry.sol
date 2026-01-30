// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ProofRegistry {
    mapping(address => mapping(uint16 => bytes32)) private proofs;

    event ProofSubmitted(address indexed user, uint16 indexed dayIndex, bytes32 proofHash);

    function submitProof(uint16 dayIndex, bytes32 proofHash) external {
        require(proofs[msg.sender][dayIndex] == bytes32(0), "already submitted");
        proofs[msg.sender][dayIndex] = proofHash;
        emit ProofSubmitted(msg.sender, dayIndex, proofHash);
    }

    function getProof(address user, uint16 dayIndex) external view returns (bytes32) {
        return proofs[user][dayIndex];
    }
}
