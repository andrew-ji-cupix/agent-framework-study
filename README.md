# Agent Framework 비교 스터디

AX 스터디 프로젝트. 에이전트 **Framework**와 **Harness**를 같은 과제로 직접 실행해 비교한다.
모델은 모두 OpenRouter의 `anthropic/claude-opus-5.5`이고, 데이터는 가상 건설 현장 mock이다.

## 바로 보기

- **핸즈온 노트북**: [handson.ipynb](handson.ipynb). 건설 현장 이슈 비서를 L1~L6으로 키운 코드의 단계별 diff, 후보 간 비교, 직접 실행. 실행 결과가 저장돼 있어 GitHub에서도 바로 보인다. 로컬에서는 `uv run --with jupyter jupyter lab handson.ipynb`
- **결론 요약**: 11개 후보 모두 모든 과제를 풀었다. 차이는 기능을 기본 지원하는지(예: 스킬은 기본 지원 +3~6줄, 직접 구현 +15줄)와 흐름을 코드로 고정하는지 모델에 맡기는지에서 났다. [단계 실험 결과](docs/05-ladder-results.md)

## 비교 대상 (2026-10-28 확정)

| 트랙 | Python | TypeScript |
| --- | --- | --- |
| Framework (7) | LangGraph, CrewAI, Strands Agents, Google ADK, OpenAI Agents SDK, Pydantic AI | Mastra |
| Harness (4) | Claude Agent SDK, Deep Agents | Pi, Flue |

팀 주력 언어가 Python이므로 Python을 우선한다. Mastra, Pi, Flue는 TypeScript 전용이다.
Flue는 Pi 하네스 위에 얹은 프레임워크라서 Harness 트랙에서 Pi와 나란히 비교한다.

## 문서

- [Agent를 무엇으로 볼 것인가](docs/01-agent-definition.md): 에이전트 정의와 출처
- [실험 설계](docs/02-experiment-plan.md): 과제, 지표, 공정성 조건, 진행 단계
- [단계 1 결과](docs/03-phase1-results.md): F1(Framework 7개), H1(Harness 4개)
- [F2·F3 결과](docs/04-f2-f3-results.md): 멀티에이전트, 사람 승인 후 재개 (Framework 7개)
- [이슈 비서 키우기 (L1~L6)](docs/05-ladder-results.md): 기본 호출 → 도구 → 스킬 → 서브에이전트 → 메모리 → 멀티에이전트 (11개 후보)

## 구조

```text
bench/       proxy.py (OpenRouter 기록 프록시), run.py (실행·채점·집계)
shared/      mock 데이터와 도구 (Python, TypeScript 포트), 과제 공통 입력, 단계 실험 프롬프트(prompts/)와 스킬(skills/)
tasks/       과제별 프롬프트, fixture, 채점기 (f1, f2, f3, h1, l1~l6)
frameworks/  Framework 후보별 프로젝트와 과제 코드 (f1~f3, l1~l6)
harnesses/   Harness 후보별 실행 코드(h1, l1~l6)와 공통 Docker 이미지
results/     실행 기록(runs/), 프록시 기록(proxy/), 집계표(summary-*.md)
```

## 실행

```sh
# 1. 프록시: OpenRouter 키는 이 프로세스에만 준다 (후보 코드에는 가짜 키만 들어간다)
OPENROUTER_API_KEY=<내 키> uv run --python 3.12 bench/proxy.py --max-cost 5

# 2. 의존성: Python 후보는 uv, TypeScript 후보는 pnpm, 하네스는 Docker 이미지
for d in frameworks/*/pyproject.toml; do uv sync --python 3.12 --project "$(dirname "$d")"; done
pnpm --dir frameworks/mastra install
docker build -t agentbench-harness harnesses

# 3. 실행과 집계
python3 bench/run.py run f1 langgraph crewai strands adk openai-agents pydantic-ai mastra --reps 3 --batch final
python3 bench/run.py run h1 claude-agent-sdk deepagents pi flue --reps 3 --batch final
python3 bench/run.py summary f1 --batch final   # f2, f3, h1도 같은 방식
python3 bench/run.py regrade f2                 # 채점기를 고친 뒤 기존 실행을 다시 채점
```
