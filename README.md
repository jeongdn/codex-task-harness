# codex-task-harness

3시간짜리 현업 과제(담당자 인터뷰 → 구현 → 검증 → 제출)를 Codex 또는 Claude Code로 진행할 때 쓰는 작업 하네스입니다.
과제 답이나 과제별 코드는 없습니다. 작업 규칙(AGENTS.md), 기록 양식, 스킬 11개, 데이터 점검·진단 도구만 들어 있습니다.

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

`setup.sh`가 하는 일 (작업 폴더에 이미 있는 파일은 건드리지 않습니다)

- 작업 폴더에 `AGENTS.md`, `CLAUDE.md`(규칙을 불러오는 한두 줄), 기록 양식 6개(`NOTES`, `INTERVIEW`, `AGREEMENT`, `PLAN`, `DESIGN`, `DECISIONS`)를 복사
- 스킬 11개를 `~/.agents/skills`(Codex)와 `~/.claude/skills`(Claude Code)에 설치. 스킬 폴더는 실행할 때마다 최신으로 덮어씁니다
- git 저장소가 아니면 `git init`. 기존 저장소면 그대로 쓰고, `.harness/`와 환경 파일은 `.git/info/exclude`로 추적에서 뺍니다. 홈 폴더가 저장소이면 맨 위의 점(.) 파일·폴더(`.ssh`, `.bash_history` 등)를 모두 뺍니다

## 단계별로 쓰는 스킬

스킬 이름 뒤에 내 의도를 한 줄 붙이면 결과가 좋아집니다. 예: `$task-intake README랑 데이터 먼저 파악해줘. 인터뷰 전에 이상한 데이터를 알고 싶어`

| 단계 | 180분 기준 | 스킬 | 남는 파일 |
|---|---|---|---|
| 파악 | 0–15분 | `$task-intake` | NOTES.md, 질문 후보 |
| 인터뷰·합의 | 15–45분 | `$task-interview` + 담당자 대화 붙여넣기 | INTERVIEW.md, AGREEMENT.md |
| 계획 | 45–55분 | `$task-plan` | PLAN.md, DESIGN.md의 전체 구조 |
| 세션 넘기기 | 55분쯤 한 번 | `$task-handoff` → `/new` | HANDOFF.md |
| 구현 | 55–145분 | `$task-build 1단계` → 설계 보고 고르기·승인 → 구현 → 3줄 설명과 확인 질문, 단계마다 반복 | 코드, tests/, DESIGN.md, DECISIONS.md |
| 검증 | 145–155분 | `$task-verify` | VERIFY.md |
| 제출 문서 | 155–165분 | `$task-submit` | 제출 문서, 후속 질문 대비 메모 |
| 설명 연습 | 165–175분 | `$task-explain 짧게` | 확인 문제식 질문 3개에 직접 답하고 피드백 |

### 설계 승인은 이렇게 답한다

`$task-build`는 설계를 보여 주고 멈춥니다. 답은 내 결정과 이유가 보이게 씁니다. 이 대화도 평가에 들어갑니다.

- 좋은 답: `B안으로 진행. 담당자가 선착순이라고 했으니 동점이면 신청 시각 순으로.`
- 좋은 답: `함수 나누는 건 좋아. 다만 거리 계산은 직선거리 말고 노선 순서로 해 줘. 진행.`
- 승인이 아닌 말: `음…`, `이게 뭐야?` (질문에 답한 뒤 다시 묻습니다)

예상 못 한 상황에서 쓰는 스킬

| 상황 | 스킬 | 하는 일 |
|---|---|---|
| 같은 오류 반복, 미리보기 안 뜸, 빙빙 돎 | `$task-unstuck` | 진단 스크립트로 상태를 모으고 원인 후보와 선택지(되돌리기 포함)를 보여 줌 |
| 남은 시간 30분 안팎, 상태가 깨짐 | `$task-rescue` | 마지막 정상 상태 확보, 범위 줄이기, 정직한 제출 문서 |
| 담당자가 요구를 바꾸거나 새로 말함 | `$task-change` | 기록·영향 범위·남은 시간 따져 계획 수정, 확인 메시지 |

## 환경 메모

- 터미널 붙여넣기는 `Ctrl+Shift+V`. Codex 입력창에서 `Ctrl+V`는 이미지 붙여넣기로 처리됩니다.
- 웹 서버는 `0.0.0.0:3000`. 오래 도는 서버는 터미널 탭을 하나 더 열어 직접 띄우는 편이 안정적입니다.
- Codex 승인 창: `y` 이번만, `p` 같은 명령은 다시 묻지 않기, `esc` 거절.
- 작업을 멈출 때는 `Esc`. 추론 수준은 `/model`에서 바꿉니다.

## 원칙

- 담당자가 말한 것만 요구사항이다. 나머지는 가정으로 적는다.
- 설계를 보고 내가 고른 뒤에 구현한다. 내가 바꾼 설계가 정답이다.
- 판정·계산은 함수와 테스트로 만들고, 담당자의 성공 기준은 꼭 테스트로 확인한다.
- 한 번에 한 단계, 단계마다 테스트와 커밋(바꾼 파일만). 되돌리기는 파일 단위로만.
- 큰 파일은 통째로 읽지 않는다. 데이터는 `profile_data.py`로 요약한다.

```bash
python3 ~/.agents/skills/task-intake/scripts/profile_data.py data/
```

## 구성

```
AGENTS.md          작업 폴더 루트에 복사되는 작업 규칙 (Claude Code는 CLAUDE.md로 불러옴)
setup.sh           설치 스크립트
templates/         기록 양식 6개
skills/            스킬 11개 (task-intake, task-interview, task-plan, task-build, task-verify, task-explain,
                   task-handoff, task-submit, task-unstuck, task-rescue, task-change)
```
