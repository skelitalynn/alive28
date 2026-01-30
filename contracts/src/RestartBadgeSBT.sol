// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract RestartBadgeSBT is ERC721, Ownable {
    uint256 private _tokenIdCounter;

    // 1 = 7 days, 2 = 14 days, 3 = 28 days
    mapping(address => uint8) public userBadgeType;

    event BadgeMinted(address indexed user, uint8 indexed badgeType, uint256 tokenId);

    constructor() ERC721("Restart Badge", "RBDG") Ownable(msg.sender) {}

    function mint(address user, uint8 badgeType) external onlyOwner {
        require(badgeType >= 1 && badgeType <= 3, "invalid badgeType");
        require(badgeType > userBadgeType[user], "already has equal or higher badge");

        _tokenIdCounter += 1;
        uint256 tokenId = _tokenIdCounter;
        userBadgeType[user] = badgeType;
        _safeMint(user, tokenId);

        emit BadgeMinted(user, badgeType, tokenId);
    }

    function badgeOf(address user) external view returns (uint8) {
        return userBadgeType[user];
    }

    function _beforeTokenTransfer(address from, address to, uint256 tokenId, uint256 batchSize)
        internal
        override
    {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        require(from == address(0) || to == address(0), "SBT: non-transferable");
    }
}
