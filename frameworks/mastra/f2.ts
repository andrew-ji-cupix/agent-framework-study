import { Agent } from "@mastra/core/agent";
import { API_KEY, BASE_URL, MODEL, save } from "../../shared/f1.ts";
import { ISSUE_ANALYST, ISSUE_DESC, PROGRESS_ANALYST, PROGRESS_DESC, PROMPT, SUPERVISOR } from "../../shared/f2.ts";
import { tools, WeeklyReport } from "./shared.ts";

const model = { providerId: "openrouter", modelId: MODEL, url: BASE_URL, apiKey: API_KEY };
const progressAnalyst = new Agent({
  id: "progress_analyst", name: "progress_analyst", description: PROGRESS_DESC,
  instructions: PROGRESS_ANALYST, model, tools: { get_progress: tools.get_progress },
});
const issueAnalyst = new Agent({
  id: "issue_analyst", name: "issue_analyst", description: ISSUE_DESC,
  instructions: ISSUE_ANALYST, model, tools: { search_issues: tools.search_issues, get_issue: tools.get_issue },
});
// agents: 하위 에이전트를 감독이 호출할 수 있는 도구로 노출한다
const supervisor = new Agent({
  id: "supervisor", name: "supervisor", instructions: SUPERVISOR, model,
  agents: { progressAnalyst, issueAnalyst },
});
const result = await supervisor.generate(PROMPT, { structuredOutput: { schema: WeeklyReport } });
save(result.object);
