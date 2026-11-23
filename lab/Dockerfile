# Seed image: the PostgreSQL 19 client tools plus what the official GoliathApp and GoliathOmics
# apply/seed scripts need (bash, git, jq, Python 3 with venv). No database runs in this image.
FROM postgres:19-bookworm
RUN apt-get update \
 && apt-get install -y --no-install-recommends bash ca-certificates curl git jq python3 python3-venv python3-pip \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /course
ENTRYPOINT ["bash", "/course/lab/bootstrap.sh"]
