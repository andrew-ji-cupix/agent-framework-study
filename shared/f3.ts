// f3.py의 TypeScript 포트 (지시문, 프롬프트, 시나리오 파일). 연결 설정은 f1.ts를 쓴다.
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const PROMPT = readFileSync(new URL("../tasks/f3/prompt.md", import.meta.url), "utf8");
export const INSTRUCTIONS = "당신은 건설 현장 이슈를 관리하는 어시스턴트입니다. 도구로 확인한 정보만 사용합니다.";
export const REJECT_MESSAGE = "현장 관리자가 이 배정을 거절했습니다. 다시 시도하지 말고 작업을 끝내세요.";
export const DIR = process.env.SCENARIO_DIR ?? ".";
export const STATE = join(DIR, "state");
export const STEP = process.argv[2] ?? "start";
export const APPROVED = process.argv[3] === "approve";

export function savePending(tool: string, args: unknown): void {
  writeFileSync(join(DIR, "pending.json"), JSON.stringify({ tool, args: typeof args === "string" ? JSON.parse(args) : args }));
}

export function saveFinal(text: string): void {
  writeFileSync(join(DIR, "final.json"), JSON.stringify({ result: text }));
}
