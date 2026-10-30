# codex-task-harness

3시간짜리 현업 과제(담당자 인터뷰 → 구현 → 검증 → 제출)를 Codex로 진행할 때 쓰는 작업 하네스입니다.
과제 답이나 과제별 코드는 없습니다. 작업 규칙(AGENTS.md), 기록 양식, Codex 스킬 6개, 데이터 점검 도구만 들어 있습니다.

## 시작 (1분)

작업 폴더에서:

```bash
git clone --depth 1 https://github.com/jeongdn/codex-task-harness.git .harness
bash .harness/setup.sh
codex
```

`setup.sh`가 하는 일 (이미 있는 파일은 건드리지 않습니다)

- 작업 폴더에 `AGENTS.md`와 기록 양식 5개(`NOTES`, `INTERVIEW`, `AGREEMENT`, `PLAN`, `DECISIONS`)를 복사
- Codex 스킬 6개를 `~/.agents/skills`에 설치
- git 저장소가 아니면 `git init`, `.harness/`는 git 추적에서 제외

## 단계별로 쓰는 스킬

| 단계 | 180분 기준 | 스킬 | 남는 파일 |
|---|---|---|---|
| 파악 | 5–15분 | `$task-intake` | NOTES.md |
| 인터뷰·합의 | 15–45분 | `$task-interview` | INTERVIEW.md, AGREEMENT.md |
| 계획 | 45–55분 | `$task-plan` | PLAN.md |
| 구현 | 55–145분 | 단계마다 테스트·커밋 | 코드, tests/, DECISIONS.md |
| 검증 | 145–160분 | `$task-verify` | VERIFY.md |
| 세션 넘기기 | 필요할 때 | `$task-handoff` | HANDOFF.md |
| 제출 준비 | 160–170분 | `$task-submit` | 제출 문서 |

스킬은 `$이름`으로 부르거나 `/skills`에서 고릅니다. 설치 직후 목록에 안 보이면 Codex를 다시 시작합니다.

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
AGENTS.md          작업 폴더 루트에 복사되는 Codex 규칙
setup.sh           설치 스크립트
templates/         기록 양식 5개
skills/            Codex 스킬 6개 (task-intake, task-interview, task-plan, task-verify, task-handoff, task-submit)
```
