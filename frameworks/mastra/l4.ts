import { join } from "node:path";
import { Agent } from "@mastra/core/agent";
import { API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, prompt, save, SKILLS } from "../../shared/ladder.ts";
import { tools } from "./shared.ts";

const model = { providerId: "openrouter", modelId: MODEL, url: BASE_URL, apiKey: API_KEY };
const progressAnalyst = new Agent({
  id: "progress_analyst", name: "progress_analyst", description: PROGRESS_DESC, instructions: PROGRESS_ANALYST,
  model, tools: { get_progress: tools.get_progress },
});
const agent = new Agent({
  id: "assistant", name: "assistant", instructions: INSTRUCTIONS, model,
  agents: { progressAnalyst },
  tools: { search_issues: tools.search_issues, get_issue: tools.get_issue, list_crew: tools.list_crew },
  skills: [join(SKILLS, "site-weekly-report")],
});
// .text에는 중간 단계의 텍스트까지 이어 붙어 나오므로 마지막 단계의 텍스트를 쓴다
const result = await agent.generate(prompt("l4"));
save(result.steps.at(-1)?.text ?? "");
