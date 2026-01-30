// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/ProofRegistry.sol";
import "../src/RestartBadgeSBT.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(pk);
        ProofRegistry registry = new ProofRegistry();
        RestartBadgeSBT sbt = new RestartBadgeSBT();
        vm.stopBroadcast();

        console2.log("ProofRegistry:", address(registry));
        console2.log("RestartBadgeSBT:", address(sbt));
    }
}
