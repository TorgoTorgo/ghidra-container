ARG GHIDRA_VERSION=latest
FROM alpine 

RUN apk --update add openjdk11 gradle unzip python3 py3-pip

RUN python3 -m pip install requests
COPY bin/ghidra-grabber.py /usr/local/bin
RUN /usr/local/bin/ghidra-grabber.py --version=${GHIDRA_VERSION} /ghidra
env GHIDRA_INSTALL_DIR=/ghidra

CMD gradle
