import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { Agent } from "@mastra/core/agent";
import { LibSQLStore } from "@mastra/libsql";
import { Memory } from "@mastra/memory";
import { API_KEY, BASE_URL, INSTRUCTIONS, MEMORY, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, prompt, save, SKILLS, STEP } from "../../shared/ladder.ts";
import { tools } from "./shared.ts";

const model = { providerId: "openrouter", modelId: MODEL, url: BASE_URL, apiKey: API_KEY };
const progressAnalyst = new Agent({
  id: "progress_analyst", name: "progress_analyst", description: PROGRESS_DESC, instructions: PROGRESS_ANALYST,
  model, tools: { get_progress: tools.get_progress },
});
mkdirSync(MEMORY, { recursive: true });
// 작업 메모리를 사용자(resource) 범위로 두면 새 대화(thread)에서도 이어진다
const memory = new Memory({
  storage: new LibSQLStore({ id: "memory", url: `file:${join(MEMORY, "memory.db")}` }),
  options: { workingMemory: { enabled: true, scope: "resource" } },
});
const agent = new Agent({
  id: "assistant", name: "assistant", instructions: INSTRUCTIONS, model,
  agents: { progressAnalyst },
  memory,
  tools: { search_issues: tools.search_issues, get_issue: tools.get_issue, list_crew: tools.list_crew },
  skills: [join(SKILLS, "site-weekly-report")],
});
// .text에는 중간 단계의 텍스트까지 이어 붙어 나오므로 마지막 단계의 텍스트를 쓴다
const result = await agent.generate(prompt(`l5-${STEP}`), { memory: { thread: `thread-${STEP}`, resource: "site-manager" } });
save(result.steps.at(-1)?.text ?? "", STEP === "remember" ? "remember" : "output");
