FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WINEPREFIX=/wine
ENV WINEARCH=win32
ENV WINEDEBUG=-all
ENV DISPLAY=:99

RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
        wine wine32:i386 wine64 \
        xvfb \
        cabextract \
        python3 python3-pip \
        zip \
        ca-certificates \
        procps \
        ffmpeg \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir flask==3.0.0 gunicorn==21.2.0

COPY setup/ /setup/
RUN chmod +x /setup/*.sh

COPY app/ /app/
WORKDIR /app

EXPOSE 5000
CMD ["/setup/entrypoint.sh"]
