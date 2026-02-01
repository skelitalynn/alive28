// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/ProofRegistry.sol";
import "../src/RestartBadgeSBT.sol";
import "../src/MilestoneNFT.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        string memory baseUri = vm.envOr("SBT_BASE_URI", string("https://api.YOUR_DOMAIN/metadata/"));
        vm.startBroadcast(pk);
        ProofRegistry registry = new ProofRegistry();
        RestartBadgeSBT sbt = new RestartBadgeSBT(address(registry), baseUri);
        MilestoneNFT milestoneNft = new MilestoneNFT();
        vm.stopBroadcast();

        console2.log("ProofRegistry:", address(registry));
        console2.log("RestartBadgeSBT:", address(sbt));
        console2.log("MilestoneNFT:", address(milestoneNft));
    }
}
