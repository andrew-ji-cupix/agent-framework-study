import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from f1 import API_KEY, BASE_URL, INSTRUCTIONS, MODEL, PROMPT, TriageReport, save  # noqa: E402
from pydantic_ai import Agent, NativeOutput  # noqa: E402
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from sitetools import get_issue, list_crew, search_issues  # noqa: E402

agent = Agent(
    OpenAIChatModel(MODEL, provider=OpenAIProvider(base_url=BASE_URL, api_key=API_KEY)),
    instructions=INSTRUCTIONS,
    tools=[search_issues, get_issue, list_crew],
    # 기본값(도구 출력)은 강제 tool_choice를 보내 Opus 5.5가 400으로 거부한다
    output_type=NativeOutput(TriageReport),
)
save(agent.run_sync(PROMPT).output)
