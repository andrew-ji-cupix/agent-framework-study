import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from ladder import ANALYST, API_KEY, BASE_URL, MODEL, REVIEWER, SKILLS, WRITER, approved, prompt, save  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402
from strands import Agent, tool  # noqa: E402
from strands.models.openai import OpenAIModel  # noqa: E402
from strands.multiagent import GraphBuilder  # noqa: E402
from strands.vended_plugins.skills import AgentSkills  # noqa: E402

model = OpenAIModel(client_args={"base_url": BASE_URL, "api_key": API_KEY}, model_id=MODEL)
analyst = Agent(name="analyst", model=model, system_prompt=ANALYST, plugins=[AgentSkills(skills=[str(SKILLS)])],
                tools=[tool(search_issues), tool(get_issue), tool(list_crew), tool(get_progress)])
writer = Agent(name="writer", model=model, system_prompt=WRITER, plugins=[AgentSkills(skills=[str(SKILLS)])])
reviewer = Agent(name="reviewer", model=model, system_prompt=REVIEWER, plugins=[AgentSkills(skills=[str(SKILLS)])])

builder = GraphBuilder()
builder.add_node(analyst, "analyst")
builder.add_node(writer, "writer")
builder.add_node(reviewer, "reviewer")
builder.add_edge("analyst", "writer")
builder.add_edge("writer", "reviewer")
# 반려되면 작성자에게 되돌린다. 작성자는 분석가의 사실과 검토 의견을 함께 입력으로 받는다
builder.add_edge("reviewer", "writer", condition=lambda state: not approved(str(state.results["reviewer"].result)))
builder.set_entry_point("analyst")
builder.reset_on_revisit(True)
builder.set_max_node_executions(7)  # 분석 1번 + 작성·검토 최대 3번
result = builder.build()(prompt("l6"))
save(str(result.results["writer"].result))
