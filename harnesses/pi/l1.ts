import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createAgentSession, DefaultResourceLoader, ModelRuntime, SessionManager } from "@earendil-works/pi-coding-agent";
import { ANTHROPIC_BASE_URL, API_KEY, INSTRUCTIONS, MODEL, prompt, save } from "/shared/ladder.ts";

// 내장 openrouter 공급자의 baseUrl만 프록시로 바꾸고, 기본 시스템 프롬프트 뒤에 지시문을 붙인다
const agentDir = mkdtempSync(join(tmpdir(), "pi-"));
writeFileSync(join(agentDir, "models.json"), JSON.stringify({ providers: { openrouter: { baseUrl: ANTHROPIC_BASE_URL, apiKey: API_KEY } } }));
const modelRuntime = await ModelRuntime.create({ modelsPath: join(agentDir, "models.json") });
const resourceLoader = new DefaultResourceLoader({ cwd: "/workspace", agentDir, appendSystemPromptOverride: (base) => [...base, INSTRUCTIONS] });
await resourceLoader.reload();
const { session } = await createAgentSession({
  cwd: "/workspace", agentDir, modelRuntime, resourceLoader,
  model: modelRuntime.getModel("openrouter", MODEL), sessionManager: SessionManager.inMemory(),
});
await session.prompt(prompt("l1"));
save(session.getLastAssistantText() ?? "");
session.dispose();
