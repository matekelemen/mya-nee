FROM python:3.8-slim-buster

WORKDIR /mya-nee

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "src/drivers/mya-nee.py" ]