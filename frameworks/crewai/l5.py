import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "shared"))

from crewai import LLM, Agent, Crew, Memory, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402
from ladder import API_KEY, BASE_URL, INSTRUCTIONS, MEMORY, MODEL, PROGRESS_ANALYST, PROGRESS_DESC, SKILLS, STEP, prompt, save  # noqa: E402
from sitetools import get_issue, get_progress, list_crew, search_issues  # noqa: E402

llm = LLM(model=f"openai/{MODEL}", base_url=BASE_URL, api_key=API_KEY)
progress_analyst = Agent(role="공정 분석가", goal=PROGRESS_ANALYST, backstory=PROGRESS_DESC, llm=llm,
                         tools=[tool(get_progress)])
assistant = Agent(role="현장 이슈 비서", goal=INSTRUCTIONS, backstory=INSTRUCTIONS, llm=llm, allow_delegation=True,
                  tools=[tool(search_issues), tool(get_issue), tool(list_crew)], skills=[SKILLS])
# 메모리: LLM이 저장할 내용을 고르고, 임베딩으로 관련 기억을 찾아 다음 실행의 과제에 넣는다
memory = Memory(llm=llm, storage=str(MEMORY / "crewai"), embedder={"provider": "openrouter", "config": {
    "api_key": API_KEY, "api_base": BASE_URL, "model_name": "openai/text-embedding-3-small"}})
# 위임은 같은 Crew에 있는 동료 에이전트에게만 할 수 있어서 Agent.kickoff 대신 Crew를 쓴다
task = Task(description=prompt(f"l5-{STEP}"), expected_output="요청에 맞는 답. 리포트 요청이면 사내 규칙에 맞는 주간 리포트",
            agent=assistant)
save(Crew(agents=[assistant, progress_analyst], tasks=[task], memory=memory).kickoff().raw, "remember" if STEP == "remember" else "output")
