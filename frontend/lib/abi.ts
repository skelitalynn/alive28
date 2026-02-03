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

export const RestartBadgeNFTABI = [
  {
    "type": "function",
    "name": "mintDay",
    "stateMutability": "nonpayable",
    "inputs": [
      { "name": "dayIndex", "type": "uint8" }
    ],
    "outputs": []
  },
  {
    "type": "function",
    "name": "composeFinal",
    "stateMutability": "nonpayable",
    "inputs": [],
    "outputs": []
  }
];
