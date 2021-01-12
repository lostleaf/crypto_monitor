FROM python:3.8.5

WORKDIR /app

ADD requirements.txt /app
RUN pip install -r requirements.txt

ADD . /app
ENV TZ=Asia/Shanghai GRAFANA_DATA_DIR=/grafana_data

CMD python app.py