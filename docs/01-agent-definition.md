# 발표 페이지: Agent를 무엇으로 볼 것인가

위치: 발표 첫 내용 페이지 (0:00–1:00). 제목에 주장 한 문장, 본문에 근거를 놓고 세부 인용은 노트와 부록으로 보낸다.

## 화면 구성 (초안)

**제목**: 에이전트를 가르는 기준은 "다음 행동을 누가 정하느냐"다

**① 주요 정의** (한 줄씩, 작은 글씨)

| 출처 | 정의 | 핵심어 |
| --- | --- | --- |
| Anthropic (2024-12) | 워크플로는 미리 정한 코드 경로로 LLM과 도구를 조율하고, 에이전트는 LLM이 과정과 도구 사용을 스스로 지휘한다 | 제어권 |
| OpenAI (2025) | 사용자를 대신해 독립적으로 작업을 완수하는 시스템 | 독립성 |
| Google Cloud (2026-04 갱신) | AI를 사용해 사용자를 대신하여 목표를 추구하고 태스크를 완료하는 소프트웨어 시스템 | 목표 |
| LangChain | LLM으로 애플리케이션의 제어 흐름을 결정하는 시스템 | 제어 흐름 |
| Simon Willison (2025-09) | 목표를 이루기 위해 도구를 루프로 실행하는 LLM | 도구·루프 |

**② 스펙트럼** (가로 막대 한 줄, Hugging Face smolagents의 agency level 표 기반)

```text
단일 호출 ── 라우터 ── 도구 호출 ── 멀티스텝 에이전트 ── 멀티에이전트
◀ 코드가 흐름을 정함 (Workflow)              LLM이 흐름을 정함 (Agent) ▶
```

**③ 이 발표의 작업 정의** (하단 강조 박스)

> 에이전트 = 목표를 받아, 도구 실행 결과를 보고 다음 행동을 LLM이 스스로 정하며 반복하는 시스템
>
> Agent = Model + Harness

## 발표자 노트 (약 60초)

에이전트라는 말을 다들 조금씩 다르게 씁니다. 출처마다 표현은 다르지만 공통 요소는 넷입니다. 목표, 도구, 루프, 그리고 LLM이 다음 행동을 정한다는 점입니다.

Anthropic은 둘 다 agentic system으로 묶되, 코드가 순서를 정하면 워크플로, LLM이 정하면 에이전트로 나눕니다. OpenAI는 단일 호출 챗봇이나 분류기는 에이전트가 아니라고 선을 긋습니다.

그래서 오늘은 "목표를 받아 도구 결과를 보며 다음 행동을 LLM이 정하는 루프"를 에이전트로 봅니다. LangChain의 표현으로는 Agent = Model + Harness입니다. 모델이 아닌 나머지 전부, 즉 시스템 프롬프트, 도구, 루프, 상태, 샌드박스가 하네스입니다.

오늘 실험도 이 구분을 따릅니다. 프레임워크는 그 루프와 흐름을 우리가 직접 짜는 도구이고, 하네스는 루프가 이미 완성되어 있어 우리는 컨텍스트와 도구만 얹는 도구입니다.

## 다음 페이지로의 연결

| 트랙 | 우리가 직접 정하는 것 | 비교 대상 |
| --- | --- | --- |
| Framework | 루프와 흐름 제어를 코드로 구성 | LangGraph, CrewAI, Strands Agents, Google ADK, OpenAI Agents SDK, Pydantic AI, Mastra |
| Harness | 완성된 루프에 컨텍스트·도구·환경만 제공 | Claude Agent SDK, Deep Agents, Pi, Flue |

## 출처 (원문, 2026-10-28 확인)

1. Anthropic, "Building effective agents", 2024-12. <https://www.anthropic.com/engineering/building-effective-agents>
   - "Workflows are systems where LLMs and tools are orchestrated through predefined code paths. Agents, on the other hand, are systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks."
   - "They are typically just LLMs using tools based on environmental feedback in a loop."
2. OpenAI, "A practical guide to building agents", 2025, p.4. <https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf>
   - "Agents are systems that independently accomplish tasks on your behalf."
   - "Applications that integrate LLMs but don't use them to control workflow execution—think simple chatbots, single-turn LLMs, or sentiment classifiers—are not agents."
3. Google Cloud, "AI 에이전트란 무엇인가요?", 2026-04-02 갱신. <https://cloud.google.com/discover/what-are-ai-agents>
   - "AI 에이전트는 AI를 사용해 사용자를 대신하여 목표를 추구하고 태스크를 완료하는 소프트웨어 시스템입니다."
4. LangChain, "What is an AI agent?". <https://blog.langchain.com/what-is-an-agent/>
   - "An AI agent is a system that uses a large language model to decide the control flow of an application."
   - "How agentic the system is depends on how much control flow the model owns."
5. Simon Willison, "I think 'agent' may finally have a widely enough agreed upon definition to be useful jargon now", 2025-09-18. <https://simonwillison.net/2025/Sep/18/agents/>
   - "An LLM agent runs tools in a loop to achieve a goal."
6. Hugging Face, smolagents 문서 "Introduction to Agents". <https://huggingface.co/docs/smolagents/conceptual_guides/intro_agents>
   - "AI Agents are programs where LLM outputs control the workflow."
   - Agency Level 표: ☆☆☆ Simple processor, ★☆☆ Router, ★★☆ Tool call, ★★☆ Multi-step Agent, ★★★ Multi-Agent, ★★★ Code Agents.
7. Vivek Trivedy (LangChain), "The Anatomy of an Agent Harness", 2026-03-10. <https://www.langchain.com/blog/the-anatomy-of-an-agent-harness>
   - "Agent = Model + Harness." / "If you're not the model, you're the harness."
   - "A raw model is not an agent. But it becomes one when a harness gives it things like state, tool execution, feedback loops, and enforceable constraints."
