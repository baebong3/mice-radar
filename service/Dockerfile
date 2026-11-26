# 저장소 루트에서 빌드한다: docker build -f service/Dockerfile -t issue-radar .
# SQLite 파일이 /data에 쌓이므로 /data에는 영구 디스크를 연결한다.
FROM python:3.12-slim
WORKDIR /app
COPY service/requirements.txt service/requirements.txt
RUN pip install --no-cache-dir -r service/requirements.txt
COPY service service
ENV RADAR_DB=/data/app.db RADAR_OUTBOX=/data/outbox RADAR_SCHEDULER=1
CMD ["sh", "-c", "uvicorn service.web:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
