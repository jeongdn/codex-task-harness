#!/usr/bin/env bash
# codex-task-harness 설치 스크립트
# 사용법: 작업 폴더에서  bash .harness/setup.sh
# 이미 있는 파일은 덮어쓰지 않는다.
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$(pwd)"
SKILLS_DIR="${HOME}/.agents/skills"

if [ "$HARNESS_DIR" = "$TARGET_DIR" ]; then
  echo "작업 폴더에서 실행하세요: bash .harness/setup.sh" >&2
  exit 1
fi

copy_if_absent() {
  local src="$1" dst="$2"
  if [ -e "$dst" ]; then
    echo "  그대로 둠  ${dst#"$TARGET_DIR"/} (이미 있음)"
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "  추가       ${dst#"$TARGET_DIR"/}"
  fi
}

echo "[1/3] 작업 규칙과 기록 양식"
if [ -e "$TARGET_DIR/AGENTS.md" ] && ! cmp -s "$HARNESS_DIR/AGENTS.md" "$TARGET_DIR/AGENTS.md"; then
  cp "$HARNESS_DIR/AGENTS.md" "$TARGET_DIR/HARNESS_RULES.md"
  echo "  주의       AGENTS.md가 이미 있어 하네스 규칙은 HARNESS_RULES.md로 저장했어요."
  echo "             내용을 확인하고 덧붙이려면: cat HARNESS_RULES.md >> AGENTS.md"
else
  copy_if_absent "$HARNESS_DIR/AGENTS.md" "$TARGET_DIR/AGENTS.md"
fi
for name in NOTES INTERVIEW AGREEMENT PLAN DECISIONS; do
  copy_if_absent "$HARNESS_DIR/templates/$name.md" "$TARGET_DIR/$name.md"
done

echo "[2/3] Codex 스킬 -> $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"
for skill in "$HARNESS_DIR"/skills/*/; do
  name="$(basename "$skill")"
  rm -rf "${SKILLS_DIR:?}/${name:?}"
  cp -R "${skill%/}" "$SKILLS_DIR/$name"
  echo "  설치       \$$name"
done

echo "[3/3] git"
if ! git -C "$TARGET_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$TARGET_DIR" init -q
  echo "  git init"
fi
GIT_DIR_ABS="$(git -C "$TARGET_DIR" rev-parse --absolute-git-dir)"
EXCLUDE_FILE="$GIT_DIR_ABS/info/exclude"
HARNESS_NAME="$(basename "$HARNESS_DIR")"
mkdir -p "$(dirname "$EXCLUDE_FILE")"
touch "$EXCLUDE_FILE"
if ! grep -qxF "$HARNESS_NAME/" "$EXCLUDE_FILE"; then
  echo "$HARNESS_NAME/" >> "$EXCLUDE_FILE"
  echo "  $HARNESS_NAME/ 를 git 추적에서 제외"
fi

echo
echo "완료. 다음: codex 실행 → /status로 모델 확인 → \$task-intake"
