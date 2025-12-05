FROM python:3.12-slim AS base

RUN groupadd -r app && useradd -r -g app app

RUN mkdir -p /myapp && chown -R app:app /myapp

COPY --chown=app:app bot_body/ /myapp/
COPY --chown=app:app requirements.txt /myapp/

RUN pip3 install --no-cache-dir -r /myapp/requirements.txt

USER app

WORKDIR /myapp

CMD ["python3", "/myapp/start.py"]
