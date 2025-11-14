FROM python:latest

RUN mkdir -p /myapp

COPY bot_body/ /myapp/
COPY requirements.txt /myapp/

RUN pip3 install -r /myapp/requirements.txt

WORKDIR /myapp
CMD ["python3", "/myapp/bot_body/start.py"]
