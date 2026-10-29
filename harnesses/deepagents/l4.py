import sys

sys.path.insert(0, "/shared")
from deepagents import create_deep_agent  # noqa: E402
from deepagents.backends import FilesystemBackend  # noqa: E402
from ladder import ANTHROPIC_BASE_URL, API_KEY, INSTRUCTIONS, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, prompt, save  # noqa: E402
from langchain_anthropic import ChatAnthropic  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

model = ChatAnthropic(model=MODEL, base_url=ANTHROPIC_BASE_URL, api_key=API_KEY, max_tokens=32000)
agent = create_deep_agent(model=model, system_prompt=INSTRUCTIONS, tools=[search_issues, get_issue, list_crew],
                          backend=FilesystemBackend(root_dir="/shared", virtual_mode=True), skills=["/skills/"],
                          subagents=[{"name": "progress-analyst", "description": PROGRESS_DESC,
                                      "system_prompt": PROGRESS_ANALYST, "tools": [get_progress]}])
result = agent.invoke({"messages": [{"role": "user", "content": prompt("l4")}]})
save(result["messages"][-1].text)
