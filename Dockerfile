ARG PYTHON_VERSION=3.8
FROM python:$PYTHON_VERSION

RUN apt-get update
RUN apt-get install -y vim-nox

WORKDIR /papis
VOLUME /papis

COPY . /papis

RUN pip install -e .[optional,develop]

CMD ["pytest", "tests", "papis", "--cov", "papis"]
