import { Agent } from "@mastra/core/agent";
import { Mastra } from "@mastra/core/mastra";
import { createTool } from "@mastra/core/tools";
import { LibSQLStore } from "@mastra/libsql";
import { API_KEY, BASE_URL, MODEL } from "../../shared/f1.ts";
import { APPROVED, INSTRUCTIONS, PROMPT, REJECT_MESSAGE, saveFinal, savePending, STATE, STEP } from "../../shared/f3.ts";
import { ASSIGN_DESC, assignIssue, assignIssueInput, tools } from "./shared.ts";

const assigner = new Agent({
  id: "assigner", name: "assigner", instructions: INSTRUCTIONS,
  model: { providerId: "openrouter", modelId: MODEL, url: BASE_URL, apiKey: API_KEY },
  tools: {
    get_issue: tools.get_issue,
    list_crew: tools.list_crew,
    // requireApproval: 실행 전에 멈추고 승인을 기다린다
    assign_issue: createTool({
      id: "assign_issue", description: ASSIGN_DESC, inputSchema: assignIssueInput, requireApproval: true,
      execute: async (input) => assignIssue(input),
    }),
  },
});
// 대기 중인 실행을 파일 DB(LibSQL)에 남겨 다른 프로세스에서 이어 간다
const mastra = new Mastra({ agents: { assigner }, storage: new LibSQLStore({ id: "f3", url: `file:${STATE}` }) });
const agent = mastra.getAgent("assigner");

if (STEP === "start") {
  const output = await agent.generate(PROMPT);
  const { toolName, args } = output.suspendPayload as { toolName: string; args: unknown };
  savePending(toolName, args);
} else {
  const { runs } = await agent.listSuspendedRuns();
  const result = APPROVED
    ? await agent.approveToolCallGenerate({ runId: runs[0].runId })
    : await agent.declineToolCallGenerate({ runId: runs[0].runId, reason: REJECT_MESSAGE });
  saveFinal(result.text);
}
