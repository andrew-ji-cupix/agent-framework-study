// f2.py의 TypeScript 포트 (지시문, 프롬프트). 연결 설정과 저장은 f1.ts를 쓴다.
import { readFileSync } from "node:fs";

export const PROMPT = readFileSync(new URL("../tasks/f2/prompt.md", import.meta.url), "utf8");
export const SUPERVISOR = "당신은 건설 현장 주간 리포트를 작성하는 감독입니다. 데이터를 직접 조회하지 않고 공정 분석가와 이슈 분석가에게 일을 맡긴 뒤 결과를 종합합니다.";
export const PROGRESS_ANALYST = "당신은 공정 분석가입니다. get_progress 도구로 확인한 공정률만 사용해 질문에 답합니다.";
export const ISSUE_ANALYST = "당신은 이슈 분석가입니다. search_issues, get_issue 도구로 확인한 이슈만 사용해 질문에 답합니다.";
export const PROGRESS_DESC = "공정 분석가에게 공정률 관련 질문을 맡긴다.";
export const ISSUE_DESC = "이슈 분석가에게 현장 이슈 관련 질문을 맡긴다.";
