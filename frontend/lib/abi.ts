export const ProofRegistryABI = [
  {
    "type": "function",
    "name": "submitProof",
    "stateMutability": "nonpayable",
    "inputs": [
      { "name": "dayIndex", "type": "uint16" },
      { "name": "proofHash", "type": "bytes32" }
    ],
    "outputs": []
  }
];

export const RestartBadgeSBTABI = [
  {
    "type": "function",
    "name": "mint",
    "stateMutability": "nonpayable",
    "inputs": [
      { "name": "user", "type": "address" },
      { "name": "badgeType", "type": "uint8" }
    ],
    "outputs": []
  }
];
