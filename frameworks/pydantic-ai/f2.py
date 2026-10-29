import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from f2 import (API_KEY, BASE_URL, ISSUE_ANALYST, MODEL, PROGRESS_ANALYST, PROMPT,  # noqa: E402
                SUPERVISOR, WeeklyReport, save)
from pydantic_ai import Agent, NativeOutput, RunContext  # noqa: E402
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from sitetools import get_issue, get_progress, search_issues  # noqa: E402

model = OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=BASE_URL, api_key=API_KEY))
progress_analyst = Agent(model, instructions=PROGRESS_ANALYST, tools=[get_progress])
issue_analyst = Agent(model, instructions=ISSUE_ANALYST, tools=[search_issues, get_issue])
supervisor = Agent(model, instructions=SUPERVISOR, output_type=NativeOutput(WeeklyReport))


# 도구 안에서 하위 에이전트를 실행한다 (Pydantic AI 문서의 agent delegation 패턴). usage를 넘겨 사용량을 합산한다
@supervisor.tool
async def ask_progress_analyst(ctx: RunContext, question: str) -> str:
    """공정 분석가에게 공정률 관련 질문을 맡긴다."""
    return (await progress_analyst.run(question, usage=ctx.usage)).output


@supervisor.tool
async def ask_issue_analyst(ctx: RunContext, question: str) -> str:
    """이슈 분석가에게 현장 이슈 관련 질문을 맡긴다."""
    return (await issue_analyst.run(question, usage=ctx.usage)).output


save(supervisor.run_sync(PROMPT).output)
