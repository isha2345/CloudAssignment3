FROM python:3.12-alpine

WORKDIR /server

COPY . /server/

RUN apk update && \
    apk add --no-cache bash && \
    pip install --no-cache-dir -r requirements.txt

RUN chmod +x run.sh

EXPOSE 5000

CMD ["./run.sh"]