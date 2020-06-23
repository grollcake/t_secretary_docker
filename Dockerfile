# Docker build:   sudo docker build -t grollcake/t_secretary:latest .
# Docker test:    sudo docker run -it --rm grollcake/t_secretary:latest /bin/bash
# Docker push:    sudo docker push grollcake/t_secretary:latest
# Docker run:     sudo docker run -d --name t_secretary  \
#                             -v <your_data_dir>:/data  \
#                             -e BOT_TOKEN=<your_token>  \
#                             -e DS_SERVER=http://172.17.0.1:5000  \
#                             -e DS_USER=<username>  \
#                             -e DS_PASS=<yourpasswords>  \
#                             -e DOWNLOAD_PATH=<yourdownloadpath>  \
#                             grollcake/t_secretary:latest

# python3 도커 이미지 사용
FROM python:3

LABEL maintainer="grollcake@gmail.com"

# 공식 이미지의 기본 작업경로는 /usr/src/app이다
WORKDIR /usr/src/app

# github로부터 내려받기
RUN apt update && apt install -y git
RUN git clone https://github.com/grollcake/t_secretary_docker.git

# 패키지 설치
WORKDIR /usr/src/app/t_secretary_docker
RUN pip install --no-cache-dir -r requirements.txt

# 볼륨설정: /data 경로에 config.json, t_secretary.log 파일을 공개한다.
VOLUME ["/data"]

# 환경변수 Set
ENV TZ="Asia/Seoul"
ENV UID=0
ENV GID=0

# 사용자 환경변수 Set
ENV BOT_TOKEN ""
ENV DS_SERVER ""
ENV DS_USER   ""
ENV DS_PASS   ""
ENV DOWNLOAD_PATH ""

# 실행
CMD ["/bin/bash", "./docker_run.sh"]

