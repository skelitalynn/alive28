pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/ProofRegistry.sol";

contract ProofRegistryTest is Test {
    uint256 validatorKey = 0xA11CE;
    address validator;
    address user = address(0xB0B);
    ProofRegistry registry;

    function setUp() public {
        validator = vm.addr(validatorKey);
        registry = new ProofRegistry(validator);
    }

    function _approval(
        uint16 dayIndex,
        bytes32 proofHash,
        uint64 deadline,
        bytes32 approvalId
    ) internal view returns (bytes memory) {
        bytes32 digest = registry.approvalDigest(
            user,
            dayIndex,
            proofHash,
            deadline,
            approvalId
        );
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(validatorKey, digest);
        return abi.encodePacked(r, s, v);
    }

    function testSubmitProofRequiresValidatorApproval() public {
        bytes32 proofHash = bytes32(uint256(1));
        bytes32 approvalId = keccak256("approval-1");
        uint64 deadline = uint64(block.timestamp + 5 minutes);

        vm.prank(user);
        vm.expectRevert();
        registry.submitProof(
            1,
            proofHash,
            deadline,
            approvalId,
            hex""
        );

        bytes memory signature = _approval(
            1,
            proofHash,
            deadline,
            approvalId
        );
        vm.prank(user);
        registry.submitProof(
            1,
            proofHash,
            deadline,
            approvalId,
            signature
        );

        assertEq(registry.getProof(user, 1), proofHash);
        assertTrue(registry.usedApprovals(approvalId));
    }

    function testApprovalIsSingleUseAndExpires() public {
        bytes32 proofHash = bytes32(uint256(2));
        bytes32 approvalId = keccak256("approval-2");
        uint64 deadline = uint64(block.timestamp + 1 minutes);
        bytes memory signature = _approval(
            2,
            proofHash,
            deadline,
            approvalId
        );

        vm.prank(user);
        registry.submitProof(
            2,
            proofHash,
            deadline,
            approvalId,
            signature
        );

        vm.prank(address(0xCAFE));
        vm.expectRevert();
        registry.submitProof(
            3,
            bytes32(uint256(3)),
            deadline,
            approvalId,
            signature
        );

        bytes32 expiredId = keccak256("expired");
        uint64 expiredDeadline = uint64(block.timestamp + 1);
        bytes memory expiredSignature = _approval(
            4,
            bytes32(uint256(4)),
            expiredDeadline,
            expiredId
        );
        vm.warp(block.timestamp + 2);
        vm.prank(user);
        vm.expectRevert();
        registry.submitProof(
            4,
            bytes32(uint256(4)),
            expiredDeadline,
            expiredId,
            expiredSignature
        );
    }

    function testSubmitProofDayIndexBounds() public {
        bytes32 proofHash = bytes32(uint256(1));
        bytes32 approvalId = keccak256("bounds");
        uint64 deadline = uint64(block.timestamp + 5 minutes);
        bytes memory signature = _approval(
            1,
            proofHash,
            deadline,
            approvalId
        );

        vm.prank(user);
        vm.expectRevert();
        registry.submitProof(
            0,
            proofHash,
            deadline,
            approvalId,
            signature
        );
        vm.prank(user);
        vm.expectRevert();
        registry.submitProof(
            29,
            proofHash,
            deadline,
            approvalId,
            signature
        );
    }
}
