FROM python:3.7.6
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
COPY COPYING COPYING.LIB DCO features.mk LICENSES Makefile README setup.py MANIFEST.in ./
ENV PYTHON_VERS python3
RUN make \
&& python3 setup.py sdist bdist_wheel \
&& pip3 install -U dist/tracecmd*.tar.gz
# RUN make \
# &&  make install_python \
# &&  cp -vn /usr/local/lib/trace-cmd/python/* /usr/local/lib/python3.7/
COPY TraceDisplay/pip3.install.txt TraceDisplay/pip3.install.txt
RUN pip3 install -r TraceDisplay/pip3.install.txt
COPY TraceDisplay TraceDisplay
RUN python3 TraceDisplay/setup.py sdist bdist_wheel \
&& pip3 install -U TraceDisplay/dist/TraceDisplay*.tar.gz
RUN patch /usr/local/lib/python3.7/site-packages/nbconvert/preprocessors/execute.py TraceDisplay/nbconvert.patch
ENTRYPOINT [ "TraceDisplay/entrypoint.sh" ]
EXPOSE 443
