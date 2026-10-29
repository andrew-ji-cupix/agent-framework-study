// Python 후보가 타입 힌트·docstring·Pydantic 모델로 얻는 도구 스키마와 출력 스키마를 TypeScript에서는 직접 선언해야 한다.
// 공정한 코드 줄 수 비교를 위해 f1.ts와 분리했다 (Python의 shared/sitetools.py, shared/f1.py에 해당).
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { assignIssue, getIssue, getProgress, listCrew, searchIssues } from "../../shared/sitetools.ts";

const trade = z.string().describe("공종. electrical, plumbing, structural, finishing, fire_protection 중 하나");

export const tools = {
  search_issues: createTool({
    id: "search_issues",
    description: "현장 이슈를 층, 공종, 상태로 검색한다. 빈 문자열인 조건은 무시한다. 요약 필드만 반환한다.",
    inputSchema: z.object({
      level: z.string().default("").describe("층. B1, 1F, 2F, 3F, 4F, RF 중 하나"),
      trade: trade.default(""),
      status: z.string().default("").describe("상태. open, in_progress, resolved 중 하나"),
    }),
    execute: async (input) => searchIssues(input),
  }),
  get_issue: createTool({
    id: "get_issue",
    description: "이슈 ID로 상세 정보(구역, 생성일 created_at, 담당자, 설명)를 조회한다.",
    inputSchema: z.object({ issue_id: z.string().describe("이슈 ID. 예: ISS-001") }),
    execute: async (input) => getIssue(input),
  }),
  list_crew: createTool({
    id: "list_crew",
    description: "공종별 작업자와 각 작업자의 현재 배정 건수(open_assignments)를 반환한다.",
    inputSchema: z.object({ trade }),
    execute: async (input) => listCrew(input),
  }),
  get_progress: createTool({
    id: "get_progress",
    description: "층별·공종별 계획 공정률(planned_pct)과 실적 공정률(actual_pct)을 반환한다.",
    inputSchema: z.object({ level: z.string().default("").describe("층. B1, 1F, 2F, 3F, 4F, RF 중 하나. 빈 문자열이면 전체 층") }),
    execute: async (input) => getProgress(input),
  }),
};

export const assignIssueInput = z.object({
  issue_id: z.string().describe("이슈 ID. 예: ISS-021"),
  assignee: z.string().describe("배정할 작업자 이름"),
});
export const ASSIGN_DESC = "이슈에 담당자를 배정한다. 배정 기록을 실제로 남기는 작업이다.";
export { assignIssue };

export const WeeklyReport = z.object({
  delayed_trades: z.array(z.object({
    level: z.string().describe("층"),
    trade: z.string().describe("공종"),
    gap: z.number().int().describe("지연 폭(%p) = planned_pct - actual_pct"),
  })).describe("계획 대비 10%p 이상 지연된 층·공종"),
  critical_by_level: z.array(z.object({
    level: z.string().describe("층"),
    count: z.number().int().describe("미해결 critical 이슈 수"),
  })).describe("층별 미해결 critical 이슈 수. 0건인 층은 제외"),
  focus_level: z.string().describe("지연 공종 수 + 미해결 critical 이슈 수가 가장 큰 층"),
  summary: z.string().describe("한국어 3~4문장 요약"),
});

export const TriageReport = z.object({
  level: z.string().describe("층. 예: 3F"),
  trade: z.string().describe("공종. 예: electrical"),
  open_count: z.number().int().describe("미해결 이슈 수"),
  critical_ids: z.array(z.string()).describe("미해결 critical 이슈 ID 목록"),
  top_priority_issue_id: z.string().describe("최우선 이슈 ID"),
  recommended_assignee: z.string().describe("추천 담당자 이름"),
  summary: z.string().describe("한국어 2~3문장 요약"),
});
