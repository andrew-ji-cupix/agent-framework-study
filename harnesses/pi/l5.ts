import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createAgentSession, DefaultResourceLoader, ModelRuntime, SessionManager } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { ANTHROPIC_BASE_URL, API_KEY, INSTRUCTIONS, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, prompt, save, SKILLS, STEP } from "/shared/ladder.ts";
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
// Pi에는 서브에이전트 기능이 없어 별도 세션(공정 분석가)을 띄워 답을 돌려주는 도구로 만든다
const getProgressTool = { name: "get_progress", label: "get_progress", description: "층별·공종별 계획 공정률(planned_pct)과 실적 공정률(actual_pct)을 반환한다.",
  parameters: Type.Object({ level: Type.Optional(Type.String({ description: "층. B1, 1F, 2F, 3F, 4F, RF 중 하나. 빈 문자열이면 전체 층" })) }),
  execute: async (_id: string, params: any) => result(getProgress(params)) };
customTools.push({ name: "ask_progress_analyst", label: "ask_progress_analyst", description: PROGRESS_DESC,
  parameters: Type.Object({ question: Type.String({ description: "공정 분석가에게 할 질문" }) }),
  execute: async (_id: string, params: any) => {
    const analyst = await newSession([getProgressTool], PROGRESS_ANALYST);
    await analyst.prompt(params.question);
    const answer = analyst.getLastAssistantText() ?? "";
    analyst.dispose();
    return result(answer);
  } } as any);
// Pi에는 메모리 기능이 없다. 작업 폴더의 AGENTS.md가 다음 세션을 시작할 때 컨텍스트 파일로 읽히는 것을 이용한다
const MEMORY_RULE = "\n다음 대화에서도 지켜야 할 사용자 요청은 /workspace/AGENTS.md에 적어 두세요.";
const session = await newSession(customTools, INSTRUCTIONS + MEMORY_RULE, [SKILLS]);
await session.prompt(prompt(`l5-${STEP}`));
save(session.getLastAssistantText() ?? "", STEP === "remember" ? "remember" : "output");
session.dispose();
