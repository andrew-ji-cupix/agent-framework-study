import { Agent } from "@mastra/core/agent";
import { API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save } from "../../shared/ladder.ts";

const agent = new Agent({
  id: "assistant", name: "assistant", instructions: INSTRUCTIONS,
  model: { providerId: "openrouter", modelId: MODEL, url: BASE_URL, apiKey: API_KEY },
});
save((await agent.generate(prompt("l1"))).text);
