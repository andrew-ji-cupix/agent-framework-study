// f1.py의 TypeScript 포트 (지시문, 프롬프트, 연결 설정, 결과 저장). 출력 스키마는 후보별 스키마 도구로 선언한다.
import { readFileSync, writeFileSync } from "node:fs";

export const INSTRUCTIONS = "당신은 건설 현장 이슈를 분석하는 어시스턴트입니다. 도구로 확인한 정보만 사용합니다.";
export const PROMPT = readFileSync(new URL("../tasks/f1/prompt.md", import.meta.url), "utf8");
export const MODEL = process.env.LLM_MODEL ?? "anthropic/claude-opus-5.5";
export const BASE_URL = process.env.LLM_BASE_URL ?? "";
export const API_KEY = process.env.LLM_API_KEY ?? "proxy";

export function save(report: unknown): void {
  writeFileSync(process.env.RESULT_PATH!, JSON.stringify(report, null, 1));
}
