ARG PYTHON_VERSION=3.11
FROM python:$PYTHON_VERSION

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install -y bash vim-nox build-essential make \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

COPY . /papis

WORKDIR /papis
RUN tools/ci-install.sh

CMD ["bash", "-c", "tools/ci-run-lint.sh && tools/ci-run-test.sh"]
