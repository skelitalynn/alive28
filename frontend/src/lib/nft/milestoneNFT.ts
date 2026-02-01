import type { Address } from "viem";

const MILESTONE_NFT_CONTRACT = (process.env.NEXT_PUBLIC_MILESTONE_NFT ||
  "0x0000000000000000000000000000000000000000") as Address;

const MILESTONE_IMAGES = [
  "/nft-assets/milestone-1.png",
  "/nft-assets/milestone-2.png",
  "/nft-assets/milestone-3.png"
];

export function getRandomMilestoneImage(): string {
  const randomIndex = Math.floor(Math.random() * MILESTONE_IMAGES.length);
  return MILESTONE_IMAGES[randomIndex];
}

function toBase64(input: string): string {
  if (typeof Buffer !== "undefined") {
    return Buffer.from(input, "utf-8").toString("base64");
  }
  // Browser fallback
  return btoa(unescape(encodeURIComponent(input)));
}

export function generateMilestoneMetadata(
  milestoneId: number,
  imageUrl: string,
  address: string,
  aiReflection?: { note: string; next: string }
): string {
  const title =
    milestoneId === 3 ? "Alive28 - Final Milestone" : `Alive28 - Milestone ${milestoneId}`;
  const description =
    milestoneId === 3
      ? "完成 28 天挑战的最终里程碑。"
      : `完成第 ${milestoneId} 个里程碑的纪念 NFT。`;

  const metadata = {
    name: title,
    description,
    image: imageUrl,
    external_url: `https://alive28.app/milestone/${milestoneId}`,
    attributes: [
      { trait_type: "Milestone", value: milestoneId },
      { trait_type: "Challenge", value: "Alive28" },
      { trait_type: "Owner", value: address },
      ...(aiReflection
        ? [
            { trait_type: "AI Reflection Note", value: aiReflection.note },
            { trait_type: "AI Reflection Next", value: aiReflection.next }
          ]
        : [])
    ]
  };

  const jsonString = JSON.stringify(metadata);
  return `data:application/json;base64,${toBase64(jsonString)}`;
}

export function getMilestoneNFTContract(): Address {
  return MILESTONE_NFT_CONTRACT;
}

export function generateTokenId(milestoneId: number, address: string): bigint {
  const hash = address.slice(2, 10);
  const timestamp = Date.now().toString().slice(-8);
  const combined = `${milestoneId}${hash}${timestamp}`;
  return BigInt(`0x${combined.padEnd(16, "0")}`);
}
