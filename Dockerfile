FROM mambaorg/micromamba:1.4.3

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

WORKDIR /app

COPY --chown=$MAMBA_USER:$MAMBA_USER api.py .

# https://docs.gunicorn.org/en/latest/settings.html
ENV GUNICORN_CMD_ARGS="--max-requests 10 --workers 2 --timeout 120 --keep-alive 15"

CMD ["gunicorn", "api:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker"]
