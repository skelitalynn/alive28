// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/ProofRegistry.sol";
import "../src/RestartBadgeNFT.sol";

contract RestartBadgeNFTTest is Test {
    uint256 validatorKey = 0xA11CE;
    ProofRegistry registry;
    RestartBadgeNFT nft;
    address user = address(0x1234);

    function setUp() public {
        registry = new ProofRegistry(vm.addr(validatorKey));
        nft = new RestartBadgeNFT(address(registry), "https://example.com/metadata/");
    }

    function _submitProof(uint16 dayIndex, bytes32 proofHash) internal {
        bytes32 approvalId = keccak256(
            abi.encodePacked("approval", dayIndex)
        );
        uint64 deadline = uint64(block.timestamp + 5 minutes);
        bytes32 digest = registry.approvalDigest(
            user,
            dayIndex,
            proofHash,
            deadline,
            approvalId
        );
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(
            validatorKey,
            digest
        );
        vm.prank(user);
        registry.submitProof(
            dayIndex,
            proofHash,
            deadline,
            approvalId,
            abi.encodePacked(r, s, v)
        );
    }

    function testMintDayRequiresProof() public {
        vm.prank(user);
        vm.expectRevert();
        nft.mintDay(1);
    }

    function testMintDayOnceAndTransferable() public {
        _submitProof(1, bytes32(uint256(1)));

        vm.prank(user);
        nft.mintDay(1);

        // cannot mint twice
        vm.prank(user);
        vm.expectRevert();
        nft.mintDay(1);

        // transferable
        uint256 tokenId = uint256(keccak256(abi.encodePacked(user, uint8(1))));
        vm.prank(user);
        nft.transferFrom(user, address(0x5678), tokenId);
    }

    function testComposeFinalRequires28AndOnlyOnce() public {
        vm.prank(user);
        vm.expectRevert();
        nft.composeFinal();

        for (uint16 i = 1; i <= 28; i++) {
            _submitProof(i, bytes32(uint256(i)));
            vm.prank(user);
            nft.mintDay(uint8(i));
        }

        vm.prank(user);
        nft.composeFinal();

        vm.prank(user);
        vm.expectRevert();
        nft.composeFinal();
    }
}
