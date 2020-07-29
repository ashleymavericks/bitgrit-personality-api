FROM python:3.6

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY / .

EXPOSE 5000

CMD [ "python", "./main.py" ]