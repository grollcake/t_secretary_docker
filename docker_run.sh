#!/bin/bash

# 24시간 단위로 재시작
while true
do
    # update from github
    git checkout -- .  # local 변경 내역 모두 취소
    git pull
    pip install --no-cache-dir -r requirements.txt

    # /data 경로에 설정파일과 로그파일 원본을 준비한다. 이미 파일이 있으면 생략한다.
    ls /data/config.json >/dev/null 2>&1 || mv config.json /data
    ls /data/t_secretary.log >/dev/null 2>&1 || touch /data/t_secretary.log

    # UID, GID를 지정했다면 소유자를 변경한다.
    chown ${UID:-0}:${GID:-0} /data/*

    # /data 경로의 파일을 실행 디렉토리로 링크를 건다.
    rm -f config.json t_secretary.log
    ln -s /data/config.json .
    ln -s /data/t_secretary.log .

    # run it
    python ./t_secretary.py &

    # 24시간 대기 (실행시간을 2초로 계산한다)
    sleep 86398
    killall python
done


