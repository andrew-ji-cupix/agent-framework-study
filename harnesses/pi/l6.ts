import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createAgentSession, DefaultResourceLoader, ModelRuntime, SessionManager } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { ANALYST, ANTHROPIC_BASE_URL, API_KEY, approved, MODEL, prompt, REVIEWER, reviewerInput, save, SKILLS, WRITER, writerInput } from "/shared/ladder.ts";
import { getIssue, getProgress, listCrew, searchIssues } from "/shared/sitetools.ts";

// 내장 openrouter 공급자의 baseUrl만 프록시로 바꾸고, 기본 시스템 프롬프트 뒤에 지시문을 붙인다
const agentDir = mkdtempSync(join(tmpdir(), "pi-"));
writeFileSync(join(agentDir, "models.json"), JSON.stringify({ providers: { openrouter: { baseUrl: ANTHROPIC_BASE_URL, apiKey: API_KEY } } }));
const modelRuntime = await ModelRuntime.create({ modelsPath: join(agentDir, "models.json") });
async function newSession(customTools: any[], instructions: string, additionalSkillPaths: string[] = []) {
  const resourceLoader = new DefaultResourceLoader({ cwd: "/workspace", agentDir, appendSystemPromptOverride: (base) => [...base, instructions], additionalSkillPaths });
  await resourceLoader.reload();
  const { session } = await createAgentSession({
    cwd: "/workspace", agentDir, modelRuntime, resourceLoader, customTools,
    model: modelRuntime.getModel("openrouter", MODEL), sessionManager: SessionManager.inMemory(),
  });
  return session;
}
const result = (value: unknown) => ({ content: [{ type: "text" as const, text: JSON.stringify(value) }], details: {} });
const trade = Type.String({ description: "공종. electrical, plumbing, structural, finishing, fire_protection 중 하나" });
const customTools = [
  { name: "search_issues", label: "search_issues", description: "현장 이슈를 층, 공종, 상태로 검색한다. 빈 문자열인 조건은 무시한다. 요약 필드만 반환한다.",
    parameters: Type.Object({ level: Type.Optional(Type.String({ description: "층. B1, 1F, 2F, 3F, 4F, RF 중 하나" })), trade: Type.Optional(trade),
      status: Type.Optional(Type.String({ description: "상태. open, in_progress, resolved 중 하나" })) }),
    execute: async (_id: string, params: any) => result(searchIssues(params)) },
  { name: "get_issue", label: "get_issue", description: "이슈 ID로 상세 정보(구역, 생성일 created_at, 담당자, 설명)를 조회한다.",
    parameters: Type.Object({ issue_id: Type.String({ description: "이슈 ID. 예: ISS-001" }) }),
    execute: async (_id: string, params: any) => result(getIssue(params)) },
  { name: "list_crew", label: "list_crew", description: "공종별 작업자와 각 작업자의 현재 배정 건수(open_assignments)를 반환한다.",
    parameters: Type.Object({ trade }), execute: async (_id: string, params: any) => result(listCrew(params)) },
];
customTools.push({ name: "get_progress", label: "get_progress", description: "층별·공종별 계획 공정률(planned_pct)과 실적 공정률(actual_pct)을 반환한다.",
  parameters: Type.Object({ level: Type.Optional(Type.String({ description: "층. B1, 1F, 2F, 3F, 4F, RF 중 하나. 빈 문자열이면 전체 층" })) }),
  execute: async (_id: string, params: any) => result(getProgress(params)) } as any);

// Pi에는 서브에이전트·그래프 기능이 없어 역할마다 세션을 새로 띄우고 순서와 반려 루프를 코드로 짠다
async function ask(tools: any[], instructions: string, text: string): Promise<string> {
  const session = await newSession(tools, instructions, [SKILLS]);
  await session.prompt(text);
  const answer = session.getLastAssistantText() ?? "";
  session.dispose();
  return answer;
}

const facts = await ask(customTools, ANALYST, prompt("l6"));
let draft = "";
let feedback = "";
for (let round = 0; round < 3; round++) {
  draft = await ask([], WRITER, writerInput(facts, feedback));
  feedback = await ask([], REVIEWER, reviewerInput(facts, draft));
  if (approved(feedback)) break;
}
save(draft);
