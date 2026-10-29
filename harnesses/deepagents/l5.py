import sys

sys.path.insert(0, "/shared")
from deepagents import create_deep_agent  # noqa: E402
from deepagents.backends import CompositeBackend, FilesystemBackend  # noqa: E402
from ladder import ANTHROPIC_BASE_URL, API_KEY, INSTRUCTIONS, MEMORY, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, STEP, prompt, save  # noqa: E402
from langchain_anthropic import ChatAnthropic  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

# 메모리: AGENTS.md는 시작할 때 시스템 프롬프트에 들어간다. 스킬(/shared)은 읽기 전용이라 /memories/만 쓰기 가능한 폴더로 연결한다
MEMORY.mkdir(exist_ok=True)
(MEMORY / "AGENTS.md").touch()
backend = CompositeBackend(default=FilesystemBackend(root_dir="/shared", virtual_mode=True),
                           routes={"/memories/": FilesystemBackend(root_dir=str(MEMORY), virtual_mode=True)})
model = ChatAnthropic(model=MODEL, base_url=ANTHROPIC_BASE_URL, api_key=API_KEY, max_tokens=32000)
agent = create_deep_agent(model=model, system_prompt=INSTRUCTIONS, tools=[search_issues, get_issue, list_crew],
                          backend=backend, skills=["/skills/"], memory=["/memories/AGENTS.md"],
                          subagents=[{"name": "progress-analyst", "description": PROGRESS_DESC,
                                      "system_prompt": PROGRESS_ANALYST, "tools": [get_progress]}])
result = agent.invoke({"messages": [{"role": "user", "content": prompt(f"l5-{STEP}")}]})
save(result["messages"][-1].text, "remember" if STEP == "remember" else "output")
