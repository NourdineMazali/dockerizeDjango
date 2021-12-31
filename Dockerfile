FROM python:3
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR /

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY . /
WORKDIR /App
