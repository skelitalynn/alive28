pragma solidity ^0.8.24;

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

    function testSubmitProofDayIndexBounds() public {
        vm.expectRevert();
        registry.submitProof(0, bytes32(uint256(1)));
        vm.expectRevert();
        registry.submitProof(29, bytes32(uint256(1)));
    }
}
