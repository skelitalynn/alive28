// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/ProofRegistry.sol";
import "../src/RestartBadgeNFT.sol";

contract RestartBadgeNFTTest is Test {
    ProofRegistry registry;
    RestartBadgeNFT nft;
    address user = address(0x1234);

    function setUp() public {
        registry = new ProofRegistry();
        nft = new RestartBadgeNFT(address(registry), "https://example.com/metadata/");
    }

    function testMintDayRequiresProof() public {
        vm.prank(user);
        vm.expectRevert();
        nft.mintDay(1);
    }

    function testMintDayOnceAndTransferable() public {
        vm.prank(user);
        registry.submitProof(1, bytes32(uint256(1)));

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
            vm.prank(user);
            registry.submitProof(i, bytes32(uint256(i)));
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
