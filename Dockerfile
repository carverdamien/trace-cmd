FROM python:2.7
WORKDIR /home/server
RUN apt update \
&&  apt install -y \
    swig
# COPY directories
COPY Documentation Documentation
COPY include include
COPY lib lib
COPY tracecmd tracecmd
COPY kernel-shark kernel-shark
COPY LICENSES LICENSES
COPY python python
COPY scripts scripts
# COPY files
COPY COPYING COPYING.LIB DCO features.mk LICENSES Makefile README ./
RUN make \
&&  make install_python \
&&  cp -vn /usr/local/lib/trace-cmd/python/* /usr/local/lib/python2.7/
COPY TraceDisplay/pip2.install.txt TraceDisplay/pip2.install.txt
RUN pip2 install -r TraceDisplay/pip2.install.txt
COPY TraceDisplay TraceDisplay
ENTRYPOINT [ "TraceDisplay/entrypoint.sh" ]
EXPOSE 443
