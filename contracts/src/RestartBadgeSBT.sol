// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

interface IProofRegistry {
    function getProof(address user, uint16 dayIndex) external view returns (bytes32);
}

contract RestartBadgeSBT is ERC721 {
    IProofRegistry public immutable proofRegistry;
    string public baseURI;

    mapping(address => mapping(uint8 => bool)) public dayMinted;
    mapping(address => uint8) public dayMintCount;
    mapping(address => bool) public finalMinted;

    event DayMinted(address indexed user, uint8 indexed dayIndex, uint256 tokenId);
    event FinalMinted(address indexed user, uint256 tokenId);

    constructor(address proofRegistry_, string memory baseURI_) ERC721("Restart Badge", "RBDG") {
        require(proofRegistry_ != address(0), "invalid registry");
        proofRegistry = IProofRegistry(proofRegistry_);
        baseURI = baseURI_;
    }

    function mintDay(uint8 dayIndex) external {
        require(dayIndex >= 1 && dayIndex <= 28, "invalid dayIndex");
        require(proofRegistry.getProof(msg.sender, dayIndex) != bytes32(0), "proof missing");
        require(!dayMinted[msg.sender][dayIndex], "already minted");

        uint256 tokenId = uint256(keccak256(abi.encodePacked(msg.sender, dayIndex)));
        dayMinted[msg.sender][dayIndex] = true;
        dayMintCount[msg.sender] += 1;

        _safeMint(msg.sender, tokenId);
        emit DayMinted(msg.sender, dayIndex, tokenId);
    }

    function composeFinal() external {
        require(dayMintCount[msg.sender] == 28, "dayMintCount not enough");
        require(!finalMinted[msg.sender], "final already minted");
        for (uint16 i = 1; i <= 28; i++) {
            require(proofRegistry.getProof(msg.sender, i) != bytes32(0), "proof missing");
        }

        uint256 tokenId = uint256(keccak256(abi.encodePacked(msg.sender, uint8(99))));
        finalMinted[msg.sender] = true;

        _safeMint(msg.sender, tokenId);
        emit FinalMinted(msg.sender, tokenId);
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        return string(abi.encodePacked(baseURI, Strings.toString(tokenId), ".json"));
    }

    function dayCount(address user) external view returns (uint8) {
        return dayMintCount[user];
    }

    function finalOf(address user) external view returns (bool) {
        return finalMinted[user];
    }

    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) {
            revert("SBT: non-transferable");
        }
        return super._update(to, tokenId, auth);
    }
}
