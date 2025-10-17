@echo off
REM create logs folder if missing
if not exist logs mkdir logs

REM build datetime string YYYYMMDD_HHMMSS
set datetime=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set datetime=%datetime: =0%

REM run bot with log redirection
chcp 65001 >nul
python -u main.py > logs\log_%datetime%.txt 2>&1
