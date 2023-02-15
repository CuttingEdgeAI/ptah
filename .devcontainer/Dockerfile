# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.183.0/containers/cpp/.devcontainer/base.Dockerfile

# [Choice] Debian / Ubuntu version: debian-10, debian-9, ubuntu-20.04, ubuntu-18.04
ARG VARIANT="bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:3.10 

ARG USERNAME=vscode

RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
    && mkdir /commandhistory \
    && touch /commandhistory/.bash_history \
    && chown -R $USERNAME /commandhistory \
    && echo "$SNIPPET" >> "/home/$USERNAME/.bashrc"

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    vim \
    python3-pip \
    python3-setuptools \
    iputils-ping

COPY library-scripts/docker-debian.sh /tmp/library-scripts/
RUN apt-get update && bash /tmp/library-scripts/docker-debian.sh

RUN pip3 install dateparser pytz yt-dlp

WORKDIR /workspaces/horus

CMD ["sleep", "infinity"]
