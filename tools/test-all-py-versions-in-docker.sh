#!/usr/bin/env bash

CTRT=docker
if command -v podman >/dev/null; then
    CTRT=podman
fi

set -ex

for pyversion in 3.8 3.9 3.10 3.11; do
    "$CTRT" build \
        --build-arg "PYTHON_VERSION=$pyversion" \
        -t "papisdev:$pyversion" \
        -t papisdev:latest \
        -f ./Dockerfile .
    "$CTRT" run --rm -it "papisdev:$pyversion"
done
