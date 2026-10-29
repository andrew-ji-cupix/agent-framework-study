import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, prompt, save  # noqa: E402
from langchain.agents import create_agent  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402

agent = create_agent(
    ChatOpenAI(model=MODEL, base_url=BASE_URL, api_key=API_KEY),
    system_prompt=INSTRUCTIONS,
    tools=[search_issues, get_issue, list_crew],
)
result = agent.invoke({"messages": [{"role": "user", "content": prompt("l2")}]})
save(result["messages"][-1].text)
