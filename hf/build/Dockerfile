FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl jq unzip ca-certificates && \
    DOWNLOAD_URL=$(curl --retry 3 --retry-delay 1 -sSLf "https://api.github.com/repos/wyeeeee/hajimi/releases/latest" | jq --raw-output '.assets[] | select(.name | endswith(".zip")) | .browser_download_url' | head -n 1) && \
    FILENAME=$(basename "${DOWNLOAD_URL}") && \
    curl -f -L -o "${FILENAME}" "${DOWNLOAD_URL}" && \
    unzip -q "${FILENAME}" && \
    rm "${FILENAME}" && \
    unzip app.zip -d app && \
    rm app.zip && \
    apt-get purge -y --auto-remove curl jq unzip && \
    rm -rf /var/lib/apt/lists/* &&\
    pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]