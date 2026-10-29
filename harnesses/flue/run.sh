#!/bin/sh
# flue run 래퍼. 사용: run.sh <과제> [단계]
# 단계 실험(l1~l6)은 /shared/prompts의 프롬프트를, 그 밖의 과제(h1)는 /task/prompt.md를 메시지로 보낸다.
task=$1 step=$2
case $task in
  l[1-6]) prompt=/shared/prompts/$task${step:+-$step}.md
          if [ "$step" = remember ]; then out=/out/remember.json; else out=/out/output.json; fi ;;
  *) prompt=/task/prompt.md out=/out/final.json ;;
esac
cd /opt/h/flue && exec node_modules/.bin/flue run "$task.ts" -m "$(cat "$prompt")" --json > "$out"
