#!/usr/bin/env bash
# Tải 2 submodule ở đúng commit đã ghim, nhưng chỉ phần skill/docs mà pipeline cần
# (remotion đầy đủ > 4 GB). Dùng trên GitHub Actions / Claude Code cloud.
# Máy local muốn bản đầy đủ: git submodule update --init
set -euo pipefail
cd "$(dirname "$0")/.."

fetch() {
  local path=$1; shift
  local url sha
  url=$(git config -f .gitmodules "submodule.$path.url")
  sha=$(git ls-tree HEAD "$path" | awk '{print $3}')
  if [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
    echo "$path: đã có, bỏ qua"
    return
  fi
  echo "$path: $url @ $sha (sparse: $*)"
  rm -rf "$path"
  git init -q "$path"
  git -C "$path" remote add origin "$url"
  git -C "$path" sparse-checkout set "$@"
  git -C "$path" fetch -q --depth 1 --filter=blob:none origin "$sha"
  git -C "$path" checkout -q FETCH_HEAD
}

fetch hyperframes skills
fetch remotion packages/skills/skills
