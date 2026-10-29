---
name: site-weekly-report
description: 현장 주간 리포트를 작성할 때 따르는 사내 형식과 규칙. 주간 리포트나 현장 리포트를 써 달라는 요청에 사용한다.
---

# 현장 주간 리포트 작성 규칙

리포트는 마크다운 기호 없이 아래 순서의 일반 텍스트 줄로 쓴다.

1. 첫 줄: `[주간 리포트] <층> <공종 한국어명>` (예: `[주간 리포트] 3F 전기`)
2. `미해결: <건수>건` — 상태가 open 또는 in_progress인 이슈 수
3. `최우선: <이슈 ID>` — 심각도가 가장 높은 미해결 이슈. 같으면 생성일(created_at)이 가장 이른 이슈
4. `담당 추천: <이름>` — 해당 공종 작업자 중 현재 배정 건수(open_assignments)가 가장 적은 사람
5. 공정 지연 정보가 있을 때만: `지연 공종: <공종 한국어명> <지연 폭>%p, ...` — 지연 폭(계획 - 실적)이 10%p 이상인 공종만, 큰 순서로
6. 요약 2~3문장
7. 마지막 줄: `문서번호: WR-<층>-<공종 코드>`

공종 한국어명: electrical=전기, plumbing=설비, structural=골조, finishing=마감, fire_protection=소방
공종 코드: electrical=EL, plumbing=PL, structural=ST, finishing=FN, fire_protection=FP
