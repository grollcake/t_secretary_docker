텔레그램을 이용한 시놀로지 다운로드 비서 봇
 
## 도커 실행
```
sudo docker run -d --name t_secretary  \
            -v <your_data_dir>:/data  \
            -e BOT_TOKEN=<your_token>  \
            -e DS_SERVER=http://172.17.0.1:5000  \
            -e DS_USER=<username>  \
            -e DS_PASS=<yourpasswords>  \
            -e DOWNLOAD_PATH=<yourdownloadpath>  \
            t_secretary:latest
```

## 텔레그램 명령어 도우미 등록
BotFather를 통해 아래 명령어를 등록한다.
```
/search - 토렌트 검색 (검색어 입력 필요)
/add - 토렌트 추가 (마그넷링크 입력 필요)
/list - 다운로드 중인 목록 보기
/popular - 인기있는 토렌트 목록
/files - 나스의 파일 목록 보기
/help - 도움말 보기
```

## 파이썬 패키지
- pysmb==1.1.27
- beautifulsoup4==4.7.1
- requests==2.18.4
- telepot==12.7

