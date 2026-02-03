// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/ProofRegistry.sol";
import "../src/RestartBadgeNFT.sol";
import "../src/MilestoneNFT.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        string memory baseUri = vm.envOr("NFT_BASE_URI", string("https://api.YOUR_DOMAIN/metadata/"));
        vm.startBroadcast(pk);
        ProofRegistry registry = new ProofRegistry();
        RestartBadgeNFT nft = new RestartBadgeNFT(address(registry), baseUri);
        MilestoneNFT milestoneNft = new MilestoneNFT();
        vm.stopBroadcast();

        console2.log("ProofRegistry:", address(registry));
        console2.log("RestartBadgeNFT:", address(nft));
        console2.log("MilestoneNFT:", address(milestoneNft));
    }
}
