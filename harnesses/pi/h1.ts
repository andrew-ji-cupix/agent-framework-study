// Pi SDK로 하네스 과제를 실행한다. 컨테이너 안에서 /workspace를 대상으로 동작한다.
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createAgentSession, ModelRuntime, SessionManager } from "@earendil-works/pi-coding-agent";

// 내장 openrouter 공급자의 baseUrl만 프록시로 바꾼다 (Claude 모델은 Anthropic 호환 엔드포인트를 쓴다)
const modelsPath = join(mkdtempSync(join(tmpdir(), "pi-")), "models.json");
writeFileSync(modelsPath, JSON.stringify({
  providers: { openrouter: { baseUrl: process.env.LLM_ANTHROPIC_BASE_URL, apiKey: process.env.LLM_API_KEY } },
}));
const modelRuntime = await ModelRuntime.create({ modelsPath });
const { session } = await createAgentSession({
  cwd: "/workspace",
  modelRuntime,
  model: modelRuntime.getModel("openrouter", process.env.LLM_MODEL!),
  sessionManager: SessionManager.inMemory(),
});
try {
  await session.prompt(readFileSync("/task/prompt.md", "utf8"));
  writeFileSync("/out/final.json", JSON.stringify({ result: session.getLastAssistantText() }));
} finally {
  session.dispose();
}
