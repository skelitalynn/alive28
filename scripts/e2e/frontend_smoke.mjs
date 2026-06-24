#!/usr/bin/env node
import http from "node:http";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { setTimeout as delay } from "node:timers/promises";

const repoRoot = new URL("../../", import.meta.url);
const frontendDirUrl = new URL("frontend/", repoRoot);
const frontendDir = fileURLToPath(frontendDirUrl);
const requireFromFrontend = createRequire(new URL("package.json", frontendDirUrl));
const { chromium } = requireFromFrontend("playwright-core");
const mockPort = Number(process.env.ALIVE28_E2E_API_PORT || "18880");
const appPort = Number(process.env.ALIVE28_E2E_APP_PORT || "3100");
const mockBase = `http://127.0.0.1:${mockPort}`;
const appBase = `http://127.0.0.1:${appPort}`;

const state = {
  log: null,
  requests: []
};
const nextLogs = [];

const task = {
  dayIndex: 1,
  title: "写下今天的一个小行动",
  instruction: "用几句话记录今天真实完成的一件小事。",
  hint: "具体一点，比完美更重要。"
};

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(payload)
  });
  res.end(payload);
}

async function readJson(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  if (!chunks.length) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf-8"));
}

function createLog(body) {
  return {
    id: "log-day-1",
    address: body.address.toLowerCase(),
    challengeId: 1,
    dayIndex: 1,
    dateKey: "2026-06-24",
    normalizedText: String(body.text || "").trim(),
    reflection: {
      note: "你把今天完成的小行动写清楚了，这就是一次有效记录。",
      next: "下一步，把这个动作再保持一分钟。"
    },
    saltHex: "0x01",
    proofHash: `0x${"12".repeat(32)}`,
    proofStatus: "ACTIVE",
    effectiveProofHash: `0x${"12".repeat(32)}`,
    status: "CREATED",
    txHash: null,
    dayNftTxHash: null,
    nftImage: null,
    createdAt: "2026-06-24T00:00:00Z"
  };
}

function startMockBackend() {
  const server = http.createServer(async (req, res) => {
    try {
      if (req.method === "OPTIONS") {
        res.writeHead(204, {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
        });
        res.end();
        return;
      }

      const url = new URL(req.url || "/", mockBase);
      state.requests.push(`${req.method} ${url.pathname}`);

      if (req.method === "GET" && url.pathname === "/health") {
        return json(res, 200, {
          status: "ok",
          version: "e2e",
          demo_mode: true,
          mode: "demo",
          ready: true,
          checks: {},
          blockingIssues: []
        });
      }

      if (req.method === "GET" && url.pathname === "/homeSnapshot") {
        return json(res, 200, {
          dayBtnLabel: "Day 1",
          dayBtnTarget: 1
        });
      }

      if (req.method === "GET" && url.pathname === "/dailySnapshot") {
        return json(res, 200, {
          dateKey: "2026-06-24",
          task,
          log: state.log,
          alreadyCheckedIn: Boolean(state.log)
        });
      }

      if (req.method === "POST" && url.pathname === "/checkin") {
        const body = await readJson(req);
        if (!body.address || !body.text) {
          return json(res, 400, {
            error: { code: "INVALID_ARGUMENT", message: "address and text required" }
          });
        }
        state.log = createLog(body);
        return json(res, 200, {
          outcome: "accepted",
          log: state.log,
          alreadyCheckedIn: false,
          message: null,
          reflection: null,
          checkinId: "e2e-checkin-id",
          recovered: false,
          execution: {
            promptVersion: "e2e",
            modelProvider: "mock",
            modelName: "mock",
            modelAttempts: 0,
            repairAttempts: 0,
            fallbackReason: null,
            nodeDurationsMs: {},
            nodeAttempts: {},
            lastError: null
          }
        });
      }

      if (req.method === "GET" && url.pathname === "/progress") {
        const completed = state.log ? [1] : [];
        return json(res, 200, {
          dateKey: "2026-06-24",
          streak: state.log ? 1 : 0,
          dayMintCount: 0,
          completedDays: completed,
          shouldMintDay: Boolean(state.log),
          mintableDayIndex: state.log ? 1 : null,
          shouldComposeFinal: false,
          finalMinted: false,
          finalNftTxHash: null
        });
      }

      return json(res, 404, {
        error: { code: "NOT_FOUND", message: `${req.method} ${url.pathname}` }
      });
    } catch (error) {
      return json(res, 500, {
        error: { code: "E2E_MOCK_ERROR", message: error?.message || String(error) }
      });
    }
  });
  server.listen(mockPort, "127.0.0.1");
  return server;
}

async function waitForHttp(url, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { cache: "no-store" });
      if (response.ok) return;
    } catch {
      // keep waiting
    }
    await delay(500);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

function sanitizeLog(text) {
  return text.replace(/[^\x09\x0a\x0d\x20-\x7e]/g, "?");
}

function recordNextLog(stream, chunk) {
  const text = sanitizeLog(chunk.toString("utf8"));
  nextLogs.push(`[next ${stream}] ${text}`);
  if (nextLogs.length > 40) nextLogs.shift();
  if (process.env.ALIVE28_E2E_VERBOSE === "1") {
    process[stream].write(`[next] ${text}`);
  }
}

function startNextDev() {
  const isWindows = process.platform === "win32";
  const command = isWindows ? process.env.ComSpec || "cmd.exe" : "npm";
  const args = isWindows
    ? ["/d", "/s", "/c", `npm run dev -- --hostname 127.0.0.1 -p ${appPort}`]
    : ["run", "dev", "--", "--hostname", "127.0.0.1", "-p", String(appPort)];
  const child = spawn(
    command,
    args,
    {
      cwd: frontendDir,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_BASE: mockBase,
        NEXT_TELEMETRY_DISABLED: "1"
      },
      stdio: ["ignore", "pipe", "pipe"]
    }
  );
  child.stdout.on("data", (chunk) => recordNextLog("stdout", chunk));
  child.stderr.on("data", (chunk) => recordNextLog("stderr", chunk));
  return child;
}

async function stopChildProcess(child) {
  if (!child || child.killed || child.exitCode !== null) return;
  if (process.platform === "win32") {
    const killer = spawn(
      process.env.ComSpec || "cmd.exe",
      ["/d", "/s", "/c", `taskkill /pid ${child.pid} /t /f`],
      { stdio: "ignore" }
    );
    await once(killer, "exit").catch(() => {});
    return;
  }
  child.kill("SIGTERM");
}

async function launchBrowser() {
  const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH;
  if (executablePath) {
    return chromium.launch({ executablePath, headless: true });
  }

  const preferred = process.env.PLAYWRIGHT_BROWSER_CHANNEL
    ? [process.env.PLAYWRIGHT_BROWSER_CHANNEL]
    : process.platform === "win32"
      ? ["msedge", "chrome"]
      : ["chrome", "chromium"];

  const errors = [];
  for (const channel of preferred) {
    try {
      return await chromium.launch({ channel, headless: true });
    } catch (error) {
      errors.push(`${channel}: ${error.message}`);
    }
  }
  throw new Error(
    "No installed browser channel was available for Playwright. " +
      "Set PLAYWRIGHT_BROWSER_CHANNEL or PLAYWRIGHT_EXECUTABLE_PATH.\n" +
      errors.join("\n")
  );
}

async function run() {
  const server = startMockBackend();
  await once(server, "listening");
  const next = startNextDev();
  let browser;
  try {
    await waitForHttp(appBase);
    browser = await launchBrowser();
    const page = await browser.newPage();
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));

    await page.goto(appBase, { waitUntil: "networkidle" });
    await page.getByTestId("demo-address-input").fill("0x1111111111111111111111111111111111111111");
    await page.getByTestId("demo-address-start").click();
    await page.getByTestId("home-day-button").click();

    await page.waitForURL("**/daily/1");
    await page.getByTestId("daily-checkin-text").fill("今天完成了第一天记录，也明确了下一步要继续保持。");
    await page.getByTestId("daily-checkin-submit").click();
    await page.getByTestId("daily-reflection-card").waitFor({ state: "visible" });
    await page.getByTestId("daily-reflection-note").waitFor({ state: "visible" });
    await page.getByTestId("daily-progress-link").click();

    await page.waitForURL("**/progress");
    await page.getByTestId("completed-day-1").waitFor({ state: "visible" });

    if (pageErrors.length) {
      throw new Error(`Browser page errors:\n${pageErrors.join("\n")}`);
    }
    const requiredRequests = ["GET /health", "GET /homeSnapshot", "GET /dailySnapshot", "POST /checkin", "GET /progress"];
    const missing = requiredRequests.filter((item) => !state.requests.includes(item));
    if (missing.length) {
      throw new Error(`Missing expected mock backend requests: ${missing.join(", ")}`);
    }
    console.log("Frontend browser smoke passed.");
  } finally {
    if (browser) await browser.close();
    await stopChildProcess(next);
    server.close();
  }
}

run().catch((error) => {
  console.error(sanitizeLog(error?.stack || error?.message || String(error)));
  if (nextLogs.length) {
    console.error(`Last Next.js logs:\n${nextLogs.join("")}`);
  }
  process.exit(1);
});
