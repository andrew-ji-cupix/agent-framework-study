import { join } from "node:path";
import { Agent } from "@mastra/core/agent";
import { API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save, SKILLS } from "../../shared/ladder.ts";
import { tools } from "./shared.ts";

const agent = new Agent({
  id: "assistant", name: "assistant", instructions: INSTRUCTIONS,
  model: { providerId: "openrouter", modelId: MODEL, url: BASE_URL, apiKey: API_KEY },
  tools: { search_issues: tools.search_issues, get_issue: tools.get_issue, list_crew: tools.list_crew },
  skills: [join(SKILLS, "site-weekly-report")],
});
// .text에는 중간 단계의 텍스트까지 이어 붙어 나오므로 마지막 단계의 텍스트를 쓴다
const result = await agent.generate(prompt("l3"));
save(result.steps.at(-1)?.text ?? "");
