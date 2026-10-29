import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from f2 import (API_KEY, BASE_URL, ISSUE_ANALYST, ISSUE_DESC, MODEL, PROGRESS_ANALYST,  # noqa: E402
                PROGRESS_DESC, PROMPT, SUPERVISOR, WeeklyReport, save)
from langchain.agents import create_agent  # noqa: E402
from langchain.agents.structured_output import ProviderStrategy  # noqa: E402
from langchain.tools import tool  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from sitetools import get_issue, get_progress, search_issues  # noqa: E402

model = ChatOpenAI(model=MODEL, base_url=BASE_URL, api_key=API_KEY)
progress_analyst = create_agent(model, tools=[get_progress], system_prompt=PROGRESS_ANALYST)
issue_analyst = create_agent(model, tools=[search_issues, get_issue], system_prompt=ISSUE_ANALYST)


# 하위 에이전트를 도구로 감싸 감독에게 준다 (LangChain 문서의 subagents-as-tools 패턴)
@tool(description=PROGRESS_DESC)
def ask_progress_analyst(question: str) -> str:
    return progress_analyst.invoke({"messages": [{"role": "user", "content": question}]})["messages"][-1].text


@tool(description=ISSUE_DESC)
def ask_issue_analyst(question: str) -> str:
    return issue_analyst.invoke({"messages": [{"role": "user", "content": question}]})["messages"][-1].text


supervisor = create_agent(model, tools=[ask_progress_analyst, ask_issue_analyst], system_prompt=SUPERVISOR,
                          response_format=ProviderStrategy(WeeklyReport))
save(supervisor.invoke({"messages": [{"role": "user", "content": PROMPT}]})["structured_response"])
