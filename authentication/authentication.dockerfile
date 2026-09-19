FROM python:3

RUN mkdir -p /opt/src/auth
WORKDIR /opt/src/auth

COPY application.py ./application.py
COPY models.py ./models.py
COPY configuration.py ./configuration.py
COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH='opt/src/authentication'

#ENTRYPOINT ["echo","hello world"]
ENTRYPOINT ["python","./application.py"]