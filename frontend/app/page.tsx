import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen p-10">
      <h1 className="text-3xl font-bold mb-4">Alive 28 MVP</h1>
      <p className="text-sm text-gray-400 mb-6">SpoonOS Graph Agent + Onchain Proof</p>
      <div className="flex gap-4">
        <Link className="px-4 py-2 bg-[#35d0ba] text-black rounded" href="/enter">进入</Link>
        <Link className="px-4 py-2 bg-[#222] rounded" href="/progress">进度</Link>
        <Link className="px-4 py-2 bg-[#222] rounded" href="/report">报告</Link>
      </div>
    </main>
  );
}
