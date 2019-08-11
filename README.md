텔레그램을 이용한 시놀로지 다운로더 비서 프로그램

# 텔레그램 봇
이름: grollcake_t_bot
토큰: 845906612:AAGoChEvwD43r8VbR5dql11UCvZepFPdV2Y
화이트리스트 관리: /start 명령어 입력 후 chatid를 보여주고 화이트리스트에 등록할 수 있도록 한다.
 

# 텔레그램 명령어
/search - 토렌트 검색 (검색어 입력 필요)
/add - 토렌트 추가 (마그넷링크 입력 필요)
/list - 다운로드 중인 목록 보기
/popular - 인기있는 토렌트 목록
/files - 나스의 파일 목록 보기
/help - 도움말 보기


# 파이썬 패키지
pysmb
beautifulsoup4==4.7.1
requests
telepot


# 토렌트 검색
토렌트왈(https://torrentwal.com/) 이용
제목, 카테고리, 해상도, 등록일자, magnet


# 개발일지
2019-03-30 개발시작
2019-03-31 토렌트 검색 모듈 개발
2019-04-01 챗봇에 /search 기능 구현
2019-04-06 /add, /list 기능 구현, 최초 배포 (우분투 서버에 배포)
2019-04-07 마그넷 버퍼 처리 (200개), /popular 구현, 버튼텍스트 말줄임 표시, /files 구현
2019-04-14 sqlite3 적용, 인기토렌트 속도 향상, /search 없이 바로 검색어 입력하기, 인기토렌트 검색 변경


# TODO
venv 환경 설정
Docker로 만들기 위한 준비
 - (완료) 환경정보를 읽는 함수 config.py 준비
 - smb 경로인 경우 챗에서 보이는 경로의 첫문자에 '/'가 빠져서 나타남
 

# 배포하기
1. cd ~/devnory && git pull
2. 라이브러리 설치: sudo pip3 install -r requirements.txt
3. supervisrod에 등록
```
    vi /etc/supervisor/supervisord.conf
    [program:t_secretary]
    command=/usr/bin/python3 /home/rollcake/devnory/chatbot/t_secretary/t_secretary.py
    user=rollcake
    environment=HOME="/home/rollcake",USER="rollcake"
    autostart=true
    autorestart=true
    stdout_logfile=/var/log/supervisord/t_secretary.log
    stdout_logfile_maxbytes=10MB
```
5. 실행하기: 
    sudo service supervisor restart
    sudo service supervisor status
    sudo supervisorctl start t_secretary
    sudo supervisorctl stop t_secretary

