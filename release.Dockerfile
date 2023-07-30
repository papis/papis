ARG PYTHON_VERSION=3.11
FROM python:$PYTHON_VERSION

# install an editor
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install --no-install-recommends -y vim-nox \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

# copy and install papis
COPY . /opt/papis
WORKDIR /opt/papis
RUN pip install .[optional] && rm -rf /opt/papis

# create environment to run papis in and set entrypoint to papis main
VOLUME /config/papis
VOLUME /library
RUN cd /root \
  && ln -s /library \
  && ln -s /library papislibrary \
  && ln -s /config .config
ENV XDG_CONFIG_HOME /config/
WORKDIR /
ENTRYPOINT ["/usr/local/bin/papis"]
