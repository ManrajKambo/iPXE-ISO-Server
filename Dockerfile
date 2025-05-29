FROM python:3.13-slim

WORKDIR /iPXE

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY iPXE.py .
COPY app.py .

COPY iPXE.tpl .

VOLUME ["/mount", "/Images.json"]

CMD ["python", "-u", "app.py"]