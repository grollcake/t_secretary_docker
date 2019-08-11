#!/bin/bash

# update from github

# /data 경로에 설정파일과 로그파일 원본을 준비한다. 이미 파일이 있으면 생략한다.
ls /data/config.json >/dev/null 2>&1 || mv config.json /data
ls /data/t_secretary.log >/dev/null 2>&1 || touch /data/t_secretary.log

# /data 경로의 파일을 실행 디렉토리로 링크를 건다.
rm -f config.json t_secretary.log
ln -s /data/config.json .
ln -s /data/t_secretary.log .

# run it
python ./t_secretary.py