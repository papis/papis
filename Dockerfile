ARG PYTHON_VERSION=3.7
FROM python:$PYTHON_VERSION

RUN apt-get update
RUN apt-get install -y vim-nox

WORKDIR /papis
VOLUME /papis

COPY . /papis

RUN python setup.py develop
RUN pip install .[develop]
RUN pip install .[optional]

CMD ["pytest", "tests", "papis", "--cov", "papis"]
