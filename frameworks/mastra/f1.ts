import { Agent } from "@mastra/core/agent";
import { API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, save } from "../../shared/f1.ts";
import { TriageReport, tools } from "./shared.ts";

const agent = new Agent({
  id: "triage",
  name: "triage",
  instructions: INSTRUCTIONS,
  model: { providerId: "openrouter", modelId: MODEL, url: BASE_URL, apiKey: API_KEY },
  tools,
});
const result = await agent.generate(PROMPT, { structuredOutput: { schema: TriageReport } });
save(result.object);
