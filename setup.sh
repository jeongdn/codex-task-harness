#!/usr/bin/env bash
# codex-task-harness 설치 스크립트
# 사용법: 작업 폴더(터미널을 처음 열었을 때의 위치, 보통 홈 ~)에서
#   git clone --depth 1 https://github.com/jeongdn/codex-task-harness.git .harness
#   bash .harness/setup.sh
# 이미 있는 파일은 덮어쓰지 않는다. 여러 번 실행해도 된다.
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$(pwd)"
CODEX_SKILLS="${HOME}/.agents/skills"
CLAUDE_SKILLS="${HOME}/.claude/skills"

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

echo "[1/3] 작업 규칙과 기록 양식 -> $TARGET_DIR"
if [ -e "$TARGET_DIR/AGENTS.md" ] && ! cmp -s "$HARNESS_DIR/AGENTS.md" "$TARGET_DIR/AGENTS.md"; then
  cp "$HARNESS_DIR/AGENTS.md" "$TARGET_DIR/HARNESS_RULES.md"
  echo "  주의       AGENTS.md가 이미 있어 하네스 규칙은 HARNESS_RULES.md로 저장했어요."
  echo "             내용을 확인하고 덧붙이려면: cat HARNESS_RULES.md >> AGENTS.md"
else
  copy_if_absent "$HARNESS_DIR/AGENTS.md" "$TARGET_DIR/AGENTS.md"
fi
# Claude Code는 CLAUDE.md를 읽는다. 같은 규칙을 쓰도록 AGENTS.md를 불러오게 한다.
if [ -e "$TARGET_DIR/CLAUDE.md" ]; then
  echo "  그대로 둠  CLAUDE.md (이미 있음)"
else
  printf '%s\n' "@AGENTS.md" > "$TARGET_DIR/CLAUDE.md"
  echo "  추가       CLAUDE.md (Claude Code용, AGENTS.md를 불러옴)"
fi
for name in NOTES INTERVIEW AGREEMENT PLAN DECISIONS; do
  copy_if_absent "$HARNESS_DIR/templates/$name.md" "$TARGET_DIR/$name.md"
done

echo "[2/3] 스킬 6개 설치"
for dest in "$CODEX_SKILLS" "$CLAUDE_SKILLS"; do
  mkdir -p "$dest"
  for skill in "$HARNESS_DIR"/skills/*/; do
    name="$(basename "$skill")"
    rm -rf "${dest:?}/${name:?}"
    cp -R "${skill%/}" "$dest/$name"
  done
done
echo "  Codex        ~/.agents/skills  (\$task-intake 처럼 부름)"
echo "  Claude Code  ~/.claude/skills  (/task-intake 처럼 부름)"

echo "[3/3] git"
if ! command -v git >/dev/null 2>&1; then
  echo "  git이 없어 건너뜀 (단계별 커밋 없이 진행)"
else
  if git -C "$TARGET_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "  기존 git 저장소 사용"
  else
    git -C "$TARGET_DIR" init -q
    echo "  git init"
  fi
  REPO_ROOT="$(git -C "$TARGET_DIR" rev-parse --show-toplevel)"
  EXCLUDE_FILE="$(git -C "$TARGET_DIR" rev-parse --absolute-git-dir)/info/exclude"
  mkdir -p "$(dirname "$EXCLUDE_FILE")"
  touch "$EXCLUDE_FILE"
  add_exclude() {
    if ! grep -qxF "$1" "$EXCLUDE_FILE"; then
      echo "$1" >> "$EXCLUDE_FILE"
      echo "  추적 제외  $1"
    fi
  }
  # 하네스 사본, 설치된 스킬, 도구 설정·캐시 폴더는 내 작업물이 아니므로 git 추적에서 뺀다.
  # (홈 폴더 자체가 작업 폴더인 환경에서 .codex 같은 설정 폴더가 커밋되지 않게 한다)
  add_exclude "$(basename "$HARNESS_DIR")/"
  for d in .agents .claude .codex .cache .config .local .npm; do
    case "$HOME/$d" in
      "$REPO_ROOT"/*) add_exclude "${HOME#"$REPO_ROOT"}/$d/" ;;
    esac
  done
  for junk in node_modules/ __pycache__/ .pytest_cache/; do
    add_exclude "$junk"
  done
fi

echo
echo "완료."
echo "  Codex        codex → /status (Agents.md 줄에 AGENTS.md가 보이면 OK) → \$task-intake"
echo "  Claude Code  claude → /task-intake"
if [ -f "$HOME/.codex/AGENTS.md" ]; then
  echo "  참고         환경이 미리 넣어 둔 Codex 규칙: ~/.codex/AGENTS.md"
fi
