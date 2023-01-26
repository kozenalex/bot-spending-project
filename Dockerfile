FROM python:latest

RUN pip3 install poetry

WORKDIR $HOME/bot_body
COPY . .
RUN poetry install

CMD ["poetry", "run", "startbot"]