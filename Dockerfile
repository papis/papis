ARG PYTHON_VERSION=3.8
FROM python:$PYTHON_VERSION

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install -y vim-nox build-essential make \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

COPY . /papis

WORKDIR /papis
RUN pip install -e .[optional,develop]

CMD ["bash", "tools/ci-run-tests.sh"]
