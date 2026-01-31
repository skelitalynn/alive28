// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/ProofRegistry.sol";
import "../src/RestartBadgeSBT.sol";

contract RestartBadgeSBTTest is Test {
    ProofRegistry registry;
    RestartBadgeSBT sbt;
    address user = address(0x1234);

    function setUp() public {
        registry = new ProofRegistry();
        sbt = new RestartBadgeSBT(address(registry), "https://example.com/metadata/");
    }

    function testMintDayRequiresProof() public {
        vm.prank(user);
        vm.expectRevert();
        sbt.mintDay(1);
    }

    function testMintDayOnceAndNonTransferable() public {
        vm.prank(user);
        registry.submitProof(1, bytes32(uint256(1)));

        vm.prank(user);
        sbt.mintDay(1);

        // cannot mint twice
        vm.prank(user);
        vm.expectRevert();
        sbt.mintDay(1);

        // non-transferable
        uint256 tokenId = uint256(keccak256(abi.encodePacked(user, uint8(1))));
        vm.prank(user);
        vm.expectRevert();
        sbt.transferFrom(user, address(0x5678), tokenId);
    }

    function testComposeFinalRequires28AndOnlyOnce() public {
        vm.prank(user);
        vm.expectRevert();
        sbt.composeFinal();

        for (uint16 i = 1; i <= 28; i++) {
            vm.prank(user);
            registry.submitProof(i, bytes32(uint256(i)));
            vm.prank(user);
            sbt.mintDay(uint8(i));
        }

        vm.prank(user);
        sbt.composeFinal();

        vm.prank(user);
        vm.expectRevert();
        sbt.composeFinal();
    }
}
