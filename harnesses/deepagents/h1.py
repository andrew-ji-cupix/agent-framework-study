"""Deep Agents로 하네스 과제를 실행한다. 컨테이너 안에서 /workspace를 대상으로 동작한다."""

import json
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_anthropic import ChatAnthropic

agent = create_deep_agent(
    # OpenRouter의 Anthropic 호환 엔드포인트(프록시 경유)
    model=ChatAnthropic(model=os.environ["LLM_MODEL"], base_url=os.environ["LLM_ANTHROPIC_BASE_URL"],
                        api_key=os.environ["LLM_API_KEY"], max_tokens=32000),
    # 실제 디스크와 셸. 격리는 컨테이너가 맡는다
    backend=LocalShellBackend(root_dir="/workspace", virtual_mode=False, inherit_env=True),
)
result = agent.invoke({"messages": [{"role": "user", "content": Path("/task/prompt.md").read_text()}]})
Path("/out/final.json").write_text(json.dumps({"result": result["messages"][-1].text}, ensure_ascii=False))
