# codex-task-harness

3시간짜리 현업 과제(담당자 인터뷰 → 구현 → 검증 → 제출)를 Codex 또는 Claude Code로 진행할 때 쓰는 작업 하네스입니다.
과제 답이나 과제별 코드는 없습니다. 작업 규칙(AGENTS.md), 기록 양식, 스킬 6개, 데이터 점검 도구만 들어 있습니다.

## 시작 (1분)

터미널을 처음 열었을 때의 위치(작업 폴더, 보통 홈 `~`)에서:

```bash
git clone --depth 1 https://github.com/jeongdn/codex-task-harness.git .harness
bash .harness/setup.sh
codex
```

확인

- 업데이트 안내가 떠도 업데이트하지 않습니다.
- `/status`의 `Agents.md` 줄에 `AGENTS.md`가 보이면 규칙이 적용된 것입니다.
- `$task`를 입력해 `task-intake` 등이 목록에 뜨면 스킬 설치가 끝난 것입니다. 안 보이면 Codex를 다시 시작합니다.
- Claude Code를 쓸 때는 `claude`를 실행하고 `/task-intake`처럼 부릅니다.

`setup.sh`가 하는 일 (이미 있는 파일은 건드리지 않습니다)

- 작업 폴더에 `AGENTS.md`, `CLAUDE.md`(AGENTS.md를 불러오는 한 줄), 기록 양식 5개(`NOTES`, `INTERVIEW`, `AGREEMENT`, `PLAN`, `DECISIONS`)를 복사
- 스킬 6개를 `~/.agents/skills`(Codex)와 `~/.claude/skills`(Claude Code)에 설치
- git 저장소가 아니면 `git init`. 기존 저장소면 그대로 쓰고, `.harness/`와 설치된 스킬 폴더, 캐시 폴더는 `.git/info/exclude`로 추적에서 제외

## 단계별로 쓰는 스킬

스킬 이름 뒤에 내 의도를 한 줄 붙이면 결과가 좋아집니다. 예: `$task-intake README랑 데이터 먼저 파악해줘. 인터뷰 전에 이상한 데이터를 알고 싶어`

| 단계 | 180분 기준 | 스킬 | 남는 파일 |
|---|---|---|---|
| 파악 | 0–15분 | `$task-intake` | NOTES.md, 질문 후보 |
| 인터뷰·합의 | 15–45분 | `$task-interview` + 담당자 대화 붙여넣기 | INTERVIEW.md, AGREEMENT.md |
| 계획 | 45–55분 | `$task-plan` | PLAN.md |
| 구현 | 55–145분 | `PLAN.md 1단계만 구현하고 테스트까지` 반복 | 코드, tests/, DECISIONS.md |
| 검증 | 145–160분 | `$task-verify` | VERIFY.md |
| 세션 넘기기 | 필요할 때 | `$task-handoff` | HANDOFF.md |
| 제출 준비 | 160–170분 | `$task-submit` | 제출 문서, 후속 질문 대비 메모 |

## 환경 메모

- 터미널 붙여넣기는 `Ctrl+Shift+V`. Codex 입력창에서 `Ctrl+V`는 이미지 붙여넣기로 처리됩니다.
- 웹 서버는 `0.0.0.0:3000`. 오래 도는 서버는 터미널 탭을 하나 더 열어 직접 띄우는 편이 안정적입니다.
- Codex 승인 창: `y` 이번만, `p` 같은 명령은 다시 묻지 않기, `esc` 거절.
- 작업을 멈출 때는 `Esc`. 추론 수준은 `/model`에서 바꿉니다.

## 원칙

- 담당자가 말한 것만 요구사항이다. 나머지는 가정으로 적는다.
- 판정·계산은 함수와 테스트로 만들고, 담당자의 성공 기준은 꼭 테스트로 확인한다.
- 한 번에 한 단계, 단계마다 테스트와 커밋.
- 큰 파일은 통째로 읽지 않는다. 데이터는 `profile_data.py`로 요약한다.

```bash
python3 ~/.agents/skills/task-intake/scripts/profile_data.py data/
```

## 구성

```
AGENTS.md          작업 폴더 루트에 복사되는 작업 규칙 (Claude Code는 CLAUDE.md로 불러옴)
setup.sh           설치 스크립트
templates/         기록 양식 5개
skills/            스킬 6개 (task-intake, task-interview, task-plan, task-verify, task-handoff, task-submit)
```
