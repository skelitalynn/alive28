import { writeContract, waitForTransactionReceipt, type Address, type PublicClient, type WalletClient } from "viem";
import { getMilestoneNFTContract, generateTokenId, getMilestoneImageForId, generateMilestoneMetadata } from "./milestoneNFT";

/**
 * Mint milestone NFT on-chain.
 * Returns txHash + imageUrl + tokenId.
 */
export async function mintMilestoneNFT(
  address: Address,
  milestoneId: number,
  publicClient: PublicClient,
  walletClient: WalletClient,
  aiReflection?: { note: string; next: string }
): Promise<{ txHash: string; imageUrl: string; tokenId: bigint }> {
  try {
    const imageUrl = getMilestoneImageForId(milestoneId as 1 | 2 | 3);
    const tokenId = generateTokenId(milestoneId, address);
    const tokenURI = generateMilestoneMetadata(milestoneId, imageUrl, address, aiReflection);

    const contractAddress = getMilestoneNFTContract();
    if (contractAddress === "0x0000000000000000000000000000000000000000") {
      throw new Error("NFT 合约地址未配置，请设置 NEXT_PUBLIC_MILESTONE_NFT");
    }

    const hash = await writeContract(walletClient, {
      address: contractAddress as Address,
      abi: [
        {
          type: "function",
          name: "mint",
          stateMutability: "nonpayable",
          inputs: [
            { name: "to", type: "address" },
            { name: "tokenId", type: "uint256" },
            { name: "tokenURI", type: "string" }
          ],
          outputs: []
        }
      ],
      functionName: "mint",
      args: [address, tokenId, tokenURI]
    });

    const receipt = await waitForTransactionReceipt(publicClient, {
      hash,
      confirmations: 1
    });

    if (receipt.status === "reverted") {
      throw new Error("交易被回滚，NFT 铸造失败");
    }

    return {
      txHash: receipt.transactionHash,
      imageUrl,
      tokenId
    };
  } catch (error: any) {
    console.error("Mint NFT error:", error);
    throw new Error(error?.message || "NFT 铸造失败");
  }
}
