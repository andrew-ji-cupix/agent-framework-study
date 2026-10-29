"""F2 과제 공통 입력: 감독과 두 분석가의 지시문, 프롬프트, 출력 스키마. 연결 설정과 저장은 f1.py를 그대로 쓴다."""

from pathlib import Path

from f1 import API_KEY, BASE_URL, MODEL, save  # noqa: F401
from pydantic import BaseModel, Field

PROMPT = (Path(__file__).parents[1] / "tasks/f2/prompt.md").read_text()
SUPERVISOR = ("당신은 건설 현장 주간 리포트를 작성하는 감독입니다. 데이터를 직접 조회하지 않고 "
              "공정 분석가와 이슈 분석가에게 일을 맡긴 뒤 결과를 종합합니다.")
PROGRESS_ANALYST = "당신은 공정 분석가입니다. get_progress 도구로 확인한 공정률만 사용해 질문에 답합니다."
ISSUE_ANALYST = "당신은 이슈 분석가입니다. search_issues, get_issue 도구로 확인한 이슈만 사용해 질문에 답합니다."
# 감독이 보는 분석가 설명 (도구 설명 또는 하위 에이전트 설명으로 쓴다)
PROGRESS_DESC = "공정 분석가에게 공정률 관련 질문을 맡긴다."
ISSUE_DESC = "이슈 분석가에게 현장 이슈 관련 질문을 맡긴다."


class DelayedTrade(BaseModel):
    level: str = Field(description="층")
    trade: str = Field(description="공종")
    gap: int = Field(description="지연 폭(%p) = planned_pct - actual_pct")


class LevelCount(BaseModel):
    level: str = Field(description="층")
    count: int = Field(description="미해결 critical 이슈 수")


class WeeklyReport(BaseModel):
    delayed_trades: list[DelayedTrade] = Field(description="계획 대비 10%p 이상 지연된 층·공종")
    critical_by_level: list[LevelCount] = Field(description="층별 미해결 critical 이슈 수. 0건인 층은 제외")
    focus_level: str = Field(description="지연 공종 수 + 미해결 critical 이슈 수가 가장 큰 층")
    summary: str = Field(description="한국어 3~4문장 요약")
