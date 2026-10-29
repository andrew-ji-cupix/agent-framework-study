import { join } from "node:path";
import { Agent } from "@mastra/core/agent";
import { createStep, createWorkflow } from "@mastra/core/workflows";
import { z } from "zod";
import { ANALYST, API_KEY, approved, BASE_URL, MODEL, prompt, REVIEWER, reviewerInput, save, SKILLS, WRITER, writerInput } from "../../shared/ladder.ts";
import { tools } from "./shared.ts";

const model = { providerId: "openrouter", modelId: MODEL, url: BASE_URL, apiKey: API_KEY };
const skills = [join(SKILLS, "site-weekly-report")];
const analyst = new Agent({
  id: "analyst", name: "analyst", instructions: ANALYST, model, skills,
  tools: { search_issues: tools.search_issues, get_issue: tools.get_issue, list_crew: tools.list_crew, get_progress: tools.get_progress },
});
const writer = new Agent({ id: "writer", name: "writer", instructions: WRITER, model, skills });
const reviewer = new Agent({ id: "reviewer", name: "reviewer", instructions: REVIEWER, model, skills });
const lastText = (result: { steps: { text: string }[] }) => result.steps.at(-1)?.text ?? "";

const Report = z.object({ facts: z.string(), draft: z.string(), feedback: z.string(), rounds: z.number() });
const analyze = createStep({
  id: "analyze", inputSchema: z.object({ request: z.string() }), outputSchema: Report,
  execute: async ({ inputData }) => ({ facts: lastText(await analyst.generate(inputData.request)), draft: "", feedback: "", rounds: 0 }),
});
const writeAndReview = createStep({
  id: "write-and-review", inputSchema: Report, outputSchema: Report,
  execute: async ({ inputData: report }) => {
    const draft = lastText(await writer.generate(writerInput(report.facts, report.feedback)));
    const feedback = lastText(await reviewer.generate(reviewerInput(report.facts, draft)));
    return { facts: report.facts, draft, feedback, rounds: report.rounds + 1 };
  },
});
// 분석 다음에 작성·검토 단계를 반려가 없을 때까지 반복한다 (최대 3번)
const workflow = createWorkflow({ id: "weekly-report", inputSchema: z.object({ request: z.string() }), outputSchema: Report })
  .then(analyze)
  .dountil(writeAndReview, async ({ inputData }) => approved(inputData.feedback) || inputData.rounds >= 3)
  .commit();
const result = await (await workflow.createRun()).start({ inputData: { request: prompt("l6") } });
save(result.status === "success" ? result.result.draft : "");
