// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * 里程碑 NFT（Week1 / Week2 / Final）
 * 前端在用户达到 7/14/28 天后调用 mint(to, tokenId, uri)，资格由后端校验并记录。
 */
contract MilestoneNFT is ERC721URIStorage, Ownable {
    constructor() ERC721("HOPE Milestone", "HOPEM") Ownable(msg.sender) {}

    /// @param to 铸造目标（必须为 msg.sender）
    /// @param tokenId 由前端按 milestoneId + address 生成
    /// @param uri 完整 data:application/json;base64,... 或 https URL
    function mint(address to, uint256 tokenId, string calldata uri) external {
        require(to == msg.sender, "can only mint for self");
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
    }
}
