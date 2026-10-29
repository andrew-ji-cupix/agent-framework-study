// ladder.py의 TypeScript 포트. 호스트와 하네스 컨테이너(/shared) 양쪽에서 쓴다.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const HERE = new URL(".", import.meta.url).pathname;
export const INSTRUCTIONS = "당신은 건설 현장 이슈 비서입니다. 확인한 정보만 사용하고 추측하지 않습니다.";
export const SKILLS = join(HERE, "skills");
export const PROGRESS_ANALYST = "당신은 공정 분석가입니다. get_progress 도구로 확인한 공정률만 사용해 질문에 답합니다.";
export const PROGRESS_DESC = "공정 분석가에게 공정률과 지연 현황을 묻는다.";
export const MODEL = process.env.LLM_MODEL ?? "anthropic/claude-opus-5.5";
export const BASE_URL = process.env.LLM_BASE_URL ?? "";
export const ANTHROPIC_BASE_URL = process.env.LLM_ANTHROPIC_BASE_URL ?? "";
export const API_KEY = process.env.LLM_API_KEY ?? "proxy";
export const OUT = dirname(process.env.RESULT_PATH ?? "/out/output.json");
export const MEMORY = join(OUT, "memory");
export const STEP = process.argv[2] ?? "";

export const prompt = (name: string): string => readFileSync(join(HERE, "prompts", `${name}.md`), "utf8");

export function save(text: string, name = "output"): void {
  writeFileSync(join(OUT, `${name}.json`), JSON.stringify({ result: text }));
}

// L6 멀티에이전트 구조: 분석가 → 작성자 → 검토자 (반려되면 작성자가 다시 고친다)
export const ANALYST = "당신은 현장 데이터 분석가입니다. 사내 '현장 주간 리포트' 규칙에 필요한 값(미해결 건수, 최우선 이슈, 담당 추천, 10%p 이상 지연된 공종과 지연 폭)을 도구로 확인해 사실 목록으로만 답합니다.";
export const WRITER = "당신은 리포트 작성자입니다. 분석가가 정리한 사실만 사용해 사내 '현장 주간 리포트' 규칙에 맞는 리포트를 쓰고, 리포트만 답합니다.";
export const REVIEWER = "당신은 리포트 검토자입니다. 사내 '현장 주간 리포트' 규칙과 분석가의 사실에 비추어 리포트를 검토합니다. 문제가 없으면 '승인'만, 고칠 점이 있으면 '반려: <고칠 점>'으로 답합니다.";
export const ORCHESTRATOR = "분석가 → 작성자 → 검토자 순서로 서브에이전트에게 일을 맡기세요. 작성자와 검토자에게는 분석가의 사실을 함께 넘기세요. 검토자가 반려하면 작성자에게 고치게 하고(최대 2번), 승인된 리포트만 그대로 답하세요.";
export const ROLE_DESC = {
  analyst: "리포트에 필요한 사실을 도구로 확인해 정리한다.",
  writer: "분석가의 사실로 사내 규칙에 맞는 리포트를 쓴다.",
  reviewer: "리포트가 사내 규칙과 분석가의 사실에 맞는지 검토한다.",
};

export function writerInput(facts: string, feedback = ""): string {
  const note = feedback ? `\n\n검토 의견(반영해서 고치세요):\n${feedback}` : "";
  return `${prompt("l6")}\n분석가의 사실:\n${facts}${note}`;
}

export const reviewerInput = (facts: string, draft: string): string => `분석가의 사실:\n${facts}\n\n리포트:\n${draft}`;
export const approved = (verdict: string): boolean => verdict.trim().startsWith("승인");
