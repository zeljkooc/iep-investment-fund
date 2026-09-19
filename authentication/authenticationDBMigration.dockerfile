FROM python:3

RUN mkdir -p /opt/src/auth
WORKDIR /opt/src/auth

COPY migrate.py ./migrate.py
COPY models.py ./models.py
COPY configuration.py ./configuration.py
COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

#ENTRYPOINT ["echo","hello world"]
ENTRYPOINT ["python","./migrate.py"]