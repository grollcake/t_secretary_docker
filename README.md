텔레그램을 이용한 시놀로지 다운로드 비서 챗봇

## 챗봇 기능
- 시놀로지의 다운로드 스테이션과 연동하여 작동한다
- 제목으로 검색하고 다운로드 할 수 있다
- 인기있는 TV를 검색하고 다운로드 할 수 있다
- 마그넷 주소를 추가하여 다운로드 할 수 있다
- 현재 다운로드 중인 목록을 확인할 수 있다
- 다운로드 받은 파일들을 탐색할 수 있다
- 시놀로지가 아닌 다른 서버에서도 Docker로도 실행할 수 있다 (동일 네트워크 대역 필요)
- Docker 컨테이너 재시작 시 자동 업데이트 한다


## 필요 사항
- 다운로드 스테이션 패키지가 설치된 시놀로지 NAS
- Docker를 구동할 수 있는 환경
- 텔레그램 봇


## 챗봇 명령어
BotFather로 명령어를 등록해놓으면 `/`를 눌렀을 때 사용 가능한 명령어를 보여준다.

`/mybots`로 챗봇을 생성한 후에 `Edit Commands`로 아래 내용을 등록한다.
```
/search - 제목 검색
/add - 마그넷 링크 추가
/list - 다운로드 중인 목록 보기
/popular - 인기있는 TV 목록
/files - 나스의 파일 목록 보기
/help - 도움말 보기
```

## 유의 사항
- 티OOO 사이트에서 예능, 드라마, TV 카테고리를 최대 20개까지만 검색한다
- 어느날 갑자기 검색이 안될 수 있다 (참고 기다리면 다른 사이트로 대체되어 다시 될 수 있다)
- 사이트가 빠르지 않기 때문에 챗봇의 답변이 좀 늦다
 
## 실행 방법 (Docker)
```
sudo docker run -d --name t_secretary  \
            --restart=always  \
            -v <your_data_dir>:/data  \
            -e BOT_TOKEN=<your_token>  \
            -e DS_SERVER=http://172.17.0.1:5000  \
            -e DS_USER=<username>  \
            -e DS_PASS=<yourpasswords>  \
            -e DOWNLOAD_PATH=<yourdownloadpath>  \
            grollcake/t_secretary:latest
```
- <your_data_dir>: config.json과 t_secretary.log 파일이 저장된다.
- BOT_TOKEN: 텔레그램 BotFather로 만든 봇의 token을 입력한다.
- DS_SERVER: 시놀로지 다운로드 스테이션의 주소를 프로토콜://호스트:포트만 입력한다.
- DS_USER: 시놀로지 다운로드 스테이션 사용자명
- DS_PASS: 시놀로지 다운로드 스테이션 암호
- DOWNLOAD_PATH: 시놀로지 다운로드 스테이션의 다운로드 경로. 공유폴더/다운로드경로 형식으로 입력한다.


## 개발 환경
- python 3.7
- 패키지 목록
 * pysmb==1.1.27
 * beautifulsoup4==4.7.1
 * requests==2.18.4
 * telepot==12.7

