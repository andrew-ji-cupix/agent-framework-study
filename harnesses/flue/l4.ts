'use agent';
import { createProvider } from '@earendil-works/pi-ai';
import { anthropicMessagesApi } from '@earendil-works/pi-ai/api/anthropic-messages.lazy';
import { openrouterProvider } from '@earendil-works/pi-ai/providers/openrouter';
import { setProvider, useModel, useSkill, useSubagent, useTool } from '@flue/runtime';
import * as v from 'valibot';
import { INSTRUCTIONS, MODEL, PROGRESS_ANALYST, PROGRESS_DESC } from '/shared/ladder.ts';
// SKILL.md import는 '/'로 시작하면 프로젝트 루트 기준으로 해석하므로 상대 경로를 쓴다
import weeklyReport from '../../../shared/skills/site-weekly-report/SKILL.md';
import { getIssue, getProgress, listCrew, searchIssues } from '/shared/sitetools.ts';

// 프록시 경유: 내장 openrouter 카탈로그를 프록시 주소로 다시 등록한다 (flue run은 app.ts를 읽지 않는다)
setProvider(
  createProvider({
    id: 'openrouter',
    auth: { apiKey: { name: 'proxy', resolve: async () => ({ auth: { apiKey: process.env.LLM_API_KEY } }) } },
    models: openrouterProvider()
      .getModels()
      .filter((model) => model.api === 'anthropic-messages')
      .map((model) => ({ ...model, baseUrl: process.env.LLM_ANTHROPIC_BASE_URL! })),
    api: anthropicMessagesApi(),
  }),
);

const trade = v.pipe(v.string(), v.description('공종. electrical, plumbing, structural, finishing, fire_protection 중 하나'));

function ProgressAnalyst() {
  useTool({
    name: 'get_progress', description: '층별·공종별 계획 공정률(planned_pct)과 실적 공정률(actual_pct)을 반환한다.',
    input: v.object({ level: v.optional(v.pipe(v.string(), v.description('층. B1, 1F, 2F, 3F, 4F, RF 중 하나. 빈 문자열이면 전체 층'))) }),
    run: async ({ data }) => ({ output: getProgress(data) }),
  });
  return PROGRESS_ANALYST;
}

export function IssueAssistant() {
  useModel(`openrouter/${MODEL}`);
  useSkill(weeklyReport);
  useSubagent({ name: 'progress-analyst', description: PROGRESS_DESC, agent: ProgressAnalyst });
  useTool({
    name: 'search_issues', description: '현장 이슈를 층, 공종, 상태로 검색한다. 빈 문자열인 조건은 무시한다. 요약 필드만 반환한다.',
    input: v.object({ level: v.optional(v.pipe(v.string(), v.description('층. B1, 1F, 2F, 3F, 4F, RF 중 하나'))), trade: v.optional(trade),
      status: v.optional(v.pipe(v.string(), v.description('상태. open, in_progress, resolved 중 하나'))) }),
    run: async ({ data }) => ({ output: searchIssues(data) }),
  });
  useTool({
    name: 'get_issue', description: '이슈 ID로 상세 정보(구역, 생성일 created_at, 담당자, 설명)를 조회한다.',
    input: v.object({ issue_id: v.pipe(v.string(), v.description('이슈 ID. 예: ISS-001')) }),
    run: async ({ data }) => ({ output: getIssue(data) }),
  });
  useTool({
    name: 'list_crew', description: '공종별 작업자와 각 작업자의 현재 배정 건수(open_assignments)를 반환한다.',
    input: v.object({ trade }), run: async ({ data }) => ({ output: listCrew(data) }),
  });
  return INSTRUCTIONS;
}
