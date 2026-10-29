현장 이슈 도구를 사용해 3층(3F) 전기(electrical) 공종의 미해결 이슈를 조사하고 우선순위 리포트를 작성하세요.

규칙:
- 미해결 이슈는 상태가 open 또는 in_progress인 이슈입니다.
- open_count: 3층 전기 공종의 미해결 이슈 수
- critical_ids: 미해결 이슈 중 심각도가 critical인 이슈 ID 목록
- top_priority_issue_id: 미해결 이슈 중 심각도가 가장 높은 이슈. 심각도가 같으면 생성일(created_at)이 가장 이른 이슈
- recommended_assignee: 전기 공종 작업자 중 현재 배정 건수(open_assignments)가 가장 적은 사람
- summary: 한국어 2~3문장 요약

추측하지 말고 도구로 확인한 정보만 사용하세요.
