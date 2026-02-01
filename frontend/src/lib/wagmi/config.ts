import { createConfig, http } from "wagmi";
import { sepolia, mainnet } from "wagmi/chains";
import { metaMask, walletConnect, injected } from "wagmi/connectors";

// 支持的链
const chains = [sepolia, mainnet] as const;

// 钱包连接器配置
const connectors = [
  metaMask(),
  walletConnect({
    projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "",
  }),
  injected(),
];

export const wagmiConfig = createConfig({
  chains,
  connectors,
  transports: {
    [sepolia.id]: http(),
    [mainnet.id]: http(),
  },
});

export { chains };
