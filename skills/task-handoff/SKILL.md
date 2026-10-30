---
name: task-handoff
description: 대화가 길어져 새 세션(Codex /new, Claude Code /clear)으로 넘어가기 전에 HANDOFF.md를 쓴다. 새 세션이 AGENTS.md와 HANDOFF.md만 읽고 바로 이어 갈 수 있게 요약한다.
---

# 세션 인계

1. `git log --oneline`, PLAN.md 상태, DECISIONS.md, 최근 테스트 결과를 확인한다.
2. 이 스킬의 `assets/HANDOFF.md` 골격으로 작업 폴더에 HANDOFF.md를 60줄 이내로 쓴다.
   목표와 성공 기준, 지금까지 한 것(커밋), 결정과 이유, 남은 일(순서대로), 주의할 함정(실패한 시도 포함), 실행·테스트 명령, 다음 세션 첫 지시문.
3. 파일 경로와 함수 이름은 정확히 쓴다. 추측은 쓰지 않는다.
4. 커밋한다: `git commit -m "[인계] HANDOFF.md / 새 세션으로 넘기기 위해"`
5. 사용자에게 안내한다: "/new(Claude Code는 /clear) 후 'AGENTS.md와 HANDOFF.md를 읽고 남은 일 1번부터 진행해'라고 입력하세요."
