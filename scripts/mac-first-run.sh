#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
project_dir="$(pwd -P)"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Run this script on the Mac that will open Unity."
  exit 1
fi

if [[ ! -f Assets/Scenes/Main.unity || ! -f Packages/manifest.json ]]; then
  echo "Unity project files are missing from $project_dir"
  exit 1
fi

unity_editor="${UNITY_EDITOR_PATH:-}"
if [[ -z "$unity_editor" ]]; then
  for candidate in /Applications/Unity/Hub/Editor/6000.*/Unity.app/Contents/MacOS/Unity; do
    if [[ -x "$candidate" ]]; then
      unity_editor="$candidate"
    fi
  done
fi

if [[ ! -x "$unity_editor" ]]; then
  echo "Install a Unity 6 editor in Unity Hub: https://unity.com/download"
  echo "If it is installed elsewhere, run with UNITY_EDITOR_PATH=/path/to/Unity."
  exit 1
fi

echo "Unity editor: $unity_editor"
echo "Project: $project_dir"

echo "Opening Unity. After import, open Assets/Scenes/Main.unity and press Play."
"$unity_editor" -projectPath "$project_dir" >/dev/null 2>&1 &
