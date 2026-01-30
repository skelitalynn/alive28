// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/ProofRegistry.sol";

contract ProofRegistryTest is Test {
    ProofRegistry registry;

    function setUp() public {
        registry = new ProofRegistry();
    }

    function testSubmitProofOnce() public {
        registry.submitProof(1, bytes32(uint256(1)));
        vm.expectRevert();
        registry.submitProof(1, bytes32(uint256(2)));
    }
}
