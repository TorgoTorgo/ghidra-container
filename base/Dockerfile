FROM alpine

RUN apk --update add openjdk11 wget unzip

ARG GHIDRA_URL
ENV GHIDRA_INSTALL_DIR /Ghidra
RUN ln -s /Ghidra/support/analyzeHeadless /usr/local/bin/ghidra
CMD /usr/local/bin/ghidra

RUN wget -O ghidra.zip $GHIDRA_URL && unzip ghidra.zip && rm ghidra.zip && mv ghidra* /Ghidra
