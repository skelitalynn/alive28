import type { Address } from "viem";

const MILESTONE_NFT_CONTRACT = (process.env.NEXT_PUBLIC_MILESTONE_NFT ||
  "0x0000000000000000000000000000000000000000") as Address;

const MILESTONE_IMAGE_BY_ID: Record<1 | 2 | 3, string> = {
  1: "/nft/week1.svg",
  2: "/nft/week2.svg",
  3: "/nft/final.svg"
};

export function getMilestoneImageForId(
  milestoneId: 1 | 2 | 3
): string {
  return MILESTONE_IMAGE_BY_ID[milestoneId];
}

export function getMilestoneNFTContract(): Address {
  return MILESTONE_NFT_CONTRACT;
}
