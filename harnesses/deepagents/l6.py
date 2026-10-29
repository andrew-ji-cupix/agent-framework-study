import sys

sys.path.insert(0, "/shared")
from deepagents import create_deep_agent  # noqa: E402
from deepagents.backends import FilesystemBackend  # noqa: E402
from ladder import (ANALYST, ANTHROPIC_BASE_URL, API_KEY, INSTRUCTIONS, MODEL, ORCHESTRATOR, REVIEWER, ROLE_DESC,  # noqa: E402
                    WRITER, prompt, save)
from langchain_anthropic import ChatAnthropic  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

model = ChatAnthropic(model=MODEL, base_url=ANTHROPIC_BASE_URL, api_key=API_KEY, max_tokens=32000)


def role(name: str, prompt_text: str, tools: list) -> dict:
    return {"name": name, "description": ROLE_DESC[name], "system_prompt": prompt_text, "tools": tools, "skills": ["/skills/"]}


# 역할별 서브에이전트. 순서와 반려 루프는 메인 에이전트가 지시문(ORCHESTRATOR)에 따라 정한다
agent = create_deep_agent(model=model, system_prompt=INSTRUCTIONS + "\n" + ORCHESTRATOR,
                          backend=FilesystemBackend(root_dir="/shared", virtual_mode=True), skills=["/skills/"],
                          subagents=[role("analyst", ANALYST, [search_issues, get_issue, list_crew, get_progress]),
                                     role("writer", WRITER, []), role("reviewer", REVIEWER, [])])
result = agent.invoke({"messages": [{"role": "user", "content": prompt("l6")}]})
save(result["messages"][-1].text)
