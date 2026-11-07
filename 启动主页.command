#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  print "未找到 Python 3，请安装后重试。"
  read -r "?按回车键关闭。"
  exit 1
fi
python3 serve.py
if [[ $? -ne 0 ]]; then
  read -r "?启动失败，请查看上方信息。按回车键关闭。"
fi
