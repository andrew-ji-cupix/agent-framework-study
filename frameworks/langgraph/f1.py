import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from f1 import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, TriageReport, save  # noqa: E402
from langchain.agents import create_agent  # noqa: E402
from langchain.agents.structured_output import ProviderStrategy  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402

agent = create_agent(
    ChatOpenAI(model=MODEL, base_url=BASE_URL, api_key=API_KEY),
    tools=[search_issues, get_issue, list_crew],
    system_prompt=INSTRUCTIONS,
    # 기본값(ToolStrategy)은 강제 tool_choice를 보내 Opus 5.5가 400으로 거부한다
    response_format=ProviderStrategy(TriageReport),
)
result = agent.invoke({"messages": [{"role": "user", "content": PROMPT}]})
save(result["structured_response"])
