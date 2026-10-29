# F2·F3 결과: 멀티에이전트와 사람 승인 후 재개

실행: 2026-10-28. 모델: OpenRouter `anthropic/claude-opus-5.5`. 후보마다 3회 반복.
F2·F3 개발 실행과 본 실행 비용은 약 $5.6이다(누적 $7.7).
원자료: [summary-f2-final.md](../results/summary-f2-final.md), [summary-f3-final.md](../results/summary-f3-final.md), `results/runs/f2-*`, `results/runs/f3-*`.

## 결론

- **F2(멀티에이전트)**: 7개 모두 3번 다 성공했다. 실행 흐름도 거의 같았다. 감독이 두 분석가를 병렬로 부르고, 분석가가 각자 도구를 쓴 뒤, 감독이 종합했다. 차이는 위임을 코드로 표현하는 방식(15~29줄)과 프롬프트 오버헤드(비용 $0.125~0.223, 1.8배)에서 났다.
- **F3(사람 승인 후 재개)**: 7개 모두 승인과 거절 두 시나리오를 3번 다 통과했다. 6개는 "도구 호출 직전에 멈춤 → 상태 저장 → 다른 프로세스에서 재개"를 기본 기능으로 지원한다. CrewAI만 도구 호출 단위로 멈추지 못해 Flow 단위의 승인으로 다시 설계해야 했다(43줄, 가장 김).
- F1~F3를 통틀어 결과(성공률, 토큰, 비용)는 비슷했다. 프레임워크를 고르는 기준은 **기능을 어떤 모양으로 제공하는가**다. 위임 방식, 승인과 상태 저장 수단, 추가 의존성, 문서와 실제 동작의 일치가 여기에 들어간다.

## F2: 감독 + 분석가 2명

| 후보 | 성공 | 시간(s) | LLM 호출 | 입력 토큰 | 출력 토큰 | 첫 요청 입력 | 비용($) | 코드 줄 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LangGraph | 3/3 | 32.7 | 7 | 16,482 | 3,914 | 1,965 | 0.144 | 22 |
| CrewAI | 3/3 | 40.6 | 7 | 23,278 | 5,302 | 2,361 | 0.223 | 18 |
| Strands Agents | 3/3 | 34.3 | 7 | 15,522 | 4,091 | 1,482 | 0.144 | 15 |
| Google ADK | 3/3 | 30.6 | 7 | 15,646 | 3,272 | 1,591 | 0.128 | 29 |
| OpenAI Agents SDK | 3/3 | 33.9 | 7 | 17,257 | 3,461 | 2,063 | 0.138 | 19 |
| Pydantic AI | 3/3 | 33.8 | 7 | 15,134 | 3,228 | 1,844 | 0.125 | 22 |
| Mastra (TS) | 3/3 | 31.7 | 6 | 16,556 | 4,060 | 2,642 | 0.153 | 19 |

과제: 공정 분석가(도구 `get_progress`)와 이슈 분석가(도구 `search_issues`, `get_issue`)에게 일을 맡겨 주간 리포트를 만든다. 감독에게는 데이터 도구를 주지 않았다. 채점 항목은 지연 공종 6건과 지연 폭, 층별 미해결 critical 건수, 두 결과를 합쳐야 나오는 집중 관리 층(3F)이다.

채점 보완: LangGraph 1회에서 감독이 공종 값을 데이터 코드(electrical) 대신 한국어("전기", "설비(배관)")로 바꿔 썼다. 프롬프트가 코드 값을 요구하지 않았으므로 채점기가 한국어 공종명과 층 표기도 같은 값으로 보도록 고쳤다. 그 뒤 F2 실행 28회 전체를 같은 기준으로 다시 채점했다(`bench/run.py regrade f2`).

### 위임을 표현하는 방식

| 후보 | 방식 | 코드 |
| --- | --- | --- |
| Strands | 에이전트를 도구로 변환 | `analyst.as_tool()` |
| OpenAI Agents SDK | 에이전트를 도구로 변환 (handoff는 제어권 자체를 넘김) | `analyst.as_tool(tool_name=..., tool_description=...)` |
| Google ADK | 에이전트를 도구로 감쌈 (`sub_agents`는 제어권을 넘김) | `AgentTool(analyst)` |
| Mastra | 하위 에이전트 등록 | `new Agent({ agents: { progressAnalyst, issueAnalyst } })` |
| CrewAI | 계층형 프로세스 (manager가 위임) | `Crew(process=Process.hierarchical, manager_agent=...)` |
| LangGraph | 하위 에이전트를 실행하는 도구 함수를 직접 작성 | `@tool` 안에서 `analyst.invoke(...)` |
| Pydantic AI | 하위 에이전트를 실행하는 도구 함수를 직접 작성 | `@supervisor.tool` 안에서 `await analyst.run(..., usage=ctx.usage)` |

### 관찰

1. **실행 흐름이 수렴했다.** 시스템 프롬프트 해시로 호출을 에이전트별로 나눠 보면, 본 실행 21회 중 15회가 같은 흐름이었다. 감독 1회 → 두 분석가 병렬(한쪽 2회, 다른 쪽 3회) → 감독 1회다. 나머지 6회는 CrewAI와 Mastra로, 분석가 호출 수가 2~4회로 조금 달랐다. "멀티에이전트 프레임워크"라는 차별점이 이 과제에서는 실행 결과로 드러나지 않았다.
2. **CrewAI는 위임 오버헤드가 가장 크다.** manager 프롬프트와 위임 도구 설명 때문에 입력 토큰이 23K로 가장 많았고, 비용은 Pydantic AI의 1.8배였다.
3. **기본 제공 여부가 코드량을 가른다.** `as_tool()`이나 `agents`처럼 위임을 기본으로 제공하면 15~19줄, LangGraph와 Pydantic AI처럼 도구 함수를 직접 쓰면 22줄이었다. ADK는 Runner·Session 준비 코드 때문에 29줄이었다.

## F3: 사람 승인 → 프로세스 종료 → 새 프로세스에서 재개

| 후보 | 성공 | 시간(s) ¹ | LLM 호출 | 입력 토큰 | 출력 토큰 | 비용($) | 코드 줄 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LangGraph | 3/3 | 18.3 | 8 | 9,433 | 585 | 0.049 | 28 |
| CrewAI | 3/3 | 28.6 | 8 | 8,299 | 887 | 0.051 | 43 |
| Strands Agents | 3/3 | 20.6 | 8 | 9,116 | 588 | 0.048 | 34 |
| Google ADK | 3/3 | 27.1 | 8 | 10,116 | 618 | 0.053 | 37 |
| OpenAI Agents SDK | 3/3 | 19.2 | 8 | 10,071 | 604 | 0.052 | 32 |
| Pydantic AI | 3/3 | 18.4 | 8 | 9,247 | 603 | 0.049 | 28 |
| Mastra (TS) | 3/3 | 19.7 | 8 | 9,859 | 593 | 0.051 | 32 |

과제: ISS-021의 담당자를 찾아 `assign_issue`로 배정한다. 실행 한 번에 두 시나리오를 돈다. 승인 시나리오는 시작 → 재개(승인), 거절 시나리오는 시작 → 재개(거절)이고, 시작과 재개는 서로 다른 프로세스다. 채점 항목은 다섯 가지다. 시작 직후 배정이 실행되지 않았는지, 대기 중인 호출의 인자(ISS-021, 이서연)가 맞는지, 새 프로세스에서 재개됐는지, 승인 시 1회·거절 시 0회 실행됐는지, 에이전트가 끝까지 응답했는지다.

¹ 실행 한 번에 프로세스를 4번 띄우므로 시작 비용이 포함된다. import 시간은 CrewAI 1.2초, ADK+LiteLLM 1.7초, 나머지는 0.4~0.65초였다.

### 승인과 상태 저장 수단

| 후보 | 도구 호출 직전에 멈춤 | 상태 저장 | 거절 메시지 지정 | 추가 설치 |
| --- | --- | --- | --- | --- |
| LangGraph | `HumanInTheLoopMiddleware` | SQLite checkpointer | 가능 | `langgraph-checkpoint-sqlite` |
| Strands | `BeforeToolCallEvent` 훅에서 `interrupt()` | `FileSessionManager` ² | 가능 | 없음 |
| Google ADK | `FunctionTool(require_confirmation=True)` | `SqliteSessionService` | **불가** (고정 문구) | 없음 |
| OpenAI Agents SDK | `function_tool(needs_approval=True)` | `RunState.to_string()`을 직접 파일로 | 가능 | 없음 |
| Pydantic AI | `Tool(requires_approval=True)` (deferred tools) | 메시지 기록 JSON을 직접 파일로 | 가능 | 없음 |
| Mastra | `createTool({ requireApproval: true })` | LibSQL 저장소 (`listSuspendedRuns`로 조회) | 가능 | `@mastra/libsql` |
| CrewAI | **지원 안 함** → Flow 단위 `@human_feedback` | `SQLiteFlowPersistence`, `Flow.from_pending()` | 코드로 처리 | 없음 |

² 재개할 때 응답해야 할 interrupt ID는 앱이 따로 보관했다(공개 API로 꺼내는 방법을 찾지 못했다). CrewAI도 재개에 쓰는 `flow_id`를 따로 보관한다.

### 관찰

1. **6개는 도구 호출 단위 승인을 기본 기능으로 갖고 있다.** 형태는 미들웨어(LangGraph), 훅(Strands), 도구 옵션(ADK, OpenAI, Pydantic AI, Mastra)으로 다르지만, 모두 "멈춘 지점의 상태를 저장했다가 결정을 넣어 이어 가기"를 지원했다.
2. **CrewAI는 설계를 바꿔야 했다.** 도구 호출 직전에 멈추는 기능은 같은 프로세스 안의 훅(콘솔 입력)뿐이었다. 프로세스를 넘는 재개는 Flow 단위로만 된다. 그래서 "에이전트가 배정안 제안 → Flow 일시정지 → 승인되면 코드가 실행"하는 구조로 구현했다. 승인 뒤 최종 메시지도 LLM이 아닌 코드가 만든다.
3. **상태 저장을 누가 맡는지가 다르다.** LangGraph, ADK, Mastra, CrewAI는 프레임워크 저장소(DB)에 맡긴다. OpenAI Agents SDK와 Pydantic AI는 직렬화한 문자열을 앱이 직접 저장한다. 앱이 저장하는 쪽은 저장소를 고를 자유가 있지만 관리 책임도 앱에 있다. OpenAI Agents SDK 문서는 직렬화된 상태를 신뢰할 수 있는 저장소에만 두라고 경고한다.

## F1~F3 종합

| 후보 | 코드 줄 (F1 / F2 / F3) | 구조화 출력 | 멀티에이전트 | 도구 단위 승인과 재개 | 설치 (패키지 / MB) ³ |
| --- | --- | --- | --- | --- | --- |
| LangGraph | 16 / 22 / 28 | 설정 변경 필요 (`ProviderStrategy`) | 직접 감쌈 | 기본 지원 (+checkpointer 패키지) | 47 / 66 |
| CrewAI | 16 / 18 / 43 | 텍스트 파싱 | 계층형 프로세스 | Flow 단위로만 | 137 / 737 |
| Strands Agents | 13 / 15 / 34 | 출력용 도구 | `as_tool()` | 기본 지원 (훅) | 54 / 94 |
| Google ADK | 27 / 29 / 37 | 출력용 도구 | `AgentTool` | 기본 지원 (거절 메시지 고정) | 88 / 285 |
| OpenAI Agents SDK | 16 / 19 / 32 | JSON schema | `as_tool()` | 기본 지원 | 38 / 65 |
| Pydantic AI | 15 / 22 / 28 | 설정 변경 필요 (`NativeOutput`) | 직접 감쌈 | 기본 지원 | 26 / 56 |
| Mastra (TS) | 12 / 19 / 32 | JSON schema | `agents` 속성 | 기본 지원 (+LibSQL 패키지) | 162 / 169 |

³ F3에 필요한 저장소 패키지를 추가한 뒤의 값이다. 그래서 단계 1 결과의 LangGraph(44 / 65), Mastra(148 / 153)보다 크다.

## DX 메모 (F2·F3에서 새로 막힌 지점)

| 후보 | 막힌 지점 | 해결 |
| --- | --- | --- |
| CrewAI | 모듈 docstring 예제의 `self.human_feedback`가 실제로는 없는 속성이었다(`AttributeError`) | `self.last_human_feedback` |
| CrewAI | 도구 호출 단위로 멈춰 프로세스를 넘겨 재개하는 기능 없음 | Flow + `@human_feedback` + 비동기 provider로 재설계 |
| Google ADK | 거절할 때 모델에게 보낼 메시지를 지정할 수 없음 | 고정 문구("This tool call is rejected")를 그대로 사용 |
| Strands | 재개 시 응답할 interrupt ID를 공개 API로 꺼내지 못함 | 시작할 때 ID를 파일로 보관 |
| LangGraph, Mastra | 파일 기반 상태 저장소가 기본 패키지에 없음 | `langgraph-checkpoint-sqlite`, `@mastra/libsql` 추가 |
| 나머지 | 없음 | F2·F3 모두 첫 시도에 동작 |

## 한계

- 과제가 쉬워서 7개 모두 성공했다. 성공률로는 구분되지 않았고, 차이는 구현 방식과 오버헤드에서 났다.
- F2는 위임 깊이가 1단계이고 분석가가 2명뿐이다. 더 복잡한 협업(분석가 사이의 대화, 반복 검토)에서는 결과가 달라질 수 있다.
- F3의 CrewAI는 다른 후보와 구조가 다르다(제안 → 승인 → 코드 실행). 같은 줄에 놓고 비교할 때 이 차이를 함께 밝혀야 한다.
- 3회 반복, 단일 모델, 기본 설정끼리의 비교다.
