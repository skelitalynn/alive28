import { createConfig, http } from "wagmi";
import { sepolia, mainnet } from "wagmi/chains";
import { walletConnect, injected } from "wagmi/connectors";

// 支持的链
const chains = [sepolia, mainnet] as const;

// 钱包连接器配置
const walletConnectProjectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID;
const connectors = [
  injected(),
  ...(walletConnectProjectId
    ? [
        walletConnect({
          projectId: walletConnectProjectId,
          metadata: {
            name: "Alive28",
            description: "28-day reflection challenge",
            url: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
            icons: []
          }
        })
      ]
    : [])
];

export const wagmiConfig = createConfig({
  chains,
  connectors,
  ssr: true,
  transports: {
    [sepolia.id]: http(),
    [mainnet.id]: http(),
  },
});

export { chains };
