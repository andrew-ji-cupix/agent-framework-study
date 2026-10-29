// sitetools.py의 TypeScript 포트. 같은 입력에 같은 출력을 낸다 (shared/parity_check.py로 확인).
import { appendFileSync, readFileSync } from "node:fs";

type Row = Record<string, string | number | null>;
const load = (name: string): Row[] => JSON.parse(readFileSync(new URL(`./data/${name}`, import.meta.url), "utf8"));
const ISSUES = load("issues.json");
const CREW = load("crew.json");
const PROGRESS = readFileSync(new URL("./data/progress.csv", import.meta.url), "utf8").trim().split("\n").slice(1)
  .map((line) => line.split(","))
  .map(([level, trade, planned, actual, as_of]) => ({ level, trade, planned_pct: Number(planned), actual_pct: Number(actual), as_of }));

export function searchIssues({ level = "", trade = "", status = "" }: { level?: string; trade?: string; status?: string }) {
  return ISSUES.filter((i) => (!level || i.level === level) && (!trade || i.trade === trade) && (!status || i.status === status))
    .map(({ id, title, level, trade, status, severity }) => ({ id, title, level, trade, status, severity }));
}

export function getIssue({ issue_id }: { issue_id: string }) {
  return ISSUES.find((i) => i.id === issue_id) ?? { error: `${issue_id} 이슈가 없습니다` };
}

export function listCrew({ trade }: { trade: string }) {
  return CREW.filter((c) => c.trade === trade);
}

export function getProgress({ level = "" }: { level?: string }) {
  return PROGRESS.filter((r) => !level || r.level === level);
}

export function assignIssue({ issue_id, assignee }: { issue_id: string; assignee: string }) {
  appendFileSync(`${process.env.SCENARIO_DIR}/assignments.jsonl`, JSON.stringify({ issue_id, assignee }) + "\n");
  return { ok: true, issue_id, assignee };
}
