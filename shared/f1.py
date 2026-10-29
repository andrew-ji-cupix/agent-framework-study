"""F1 과제 공통 입력(지시문, 프롬프트, 출력 스키마)과 결과 저장."""

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

INSTRUCTIONS = "당신은 건설 현장 이슈를 분석하는 어시스턴트입니다. 도구로 확인한 정보만 사용합니다."
PROMPT = (Path(__file__).parents[1] / "tasks/f1/prompt.md").read_text()
MODEL = os.environ.get("LLM_MODEL", "anthropic/claude-opus-5.5")
BASE_URL = os.environ.get("LLM_BASE_URL", "")  # OpenAI 호환 엔드포인트 (프록시)
API_KEY = os.environ.get("LLM_API_KEY", "proxy")  # 가짜 키. 실제 키는 프록시가 주입한다


class TriageReport(BaseModel):
    level: str = Field(description="층. 예: 3F")
    trade: str = Field(description="공종. 예: electrical")
    open_count: int = Field(description="미해결 이슈 수")
    critical_ids: list[str] = Field(description="미해결 critical 이슈 ID 목록")
    top_priority_issue_id: str = Field(description="최우선 이슈 ID")
    recommended_assignee: str = Field(description="추천 담당자 이름")
    summary: str = Field(description="한국어 2~3문장 요약")


def save(report: BaseModel | dict) -> None:
    data = report.model_dump() if isinstance(report, BaseModel) else report
    Path(os.environ["RESULT_PATH"]).write_text(json.dumps(data, ensure_ascii=False, indent=1))
