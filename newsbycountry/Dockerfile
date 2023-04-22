FROM python:3.10.10-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt /code/

RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

COPY . /code/

RUN chmod +x ./scripts/*.sh
ENTRYPOINT [ "./scripts/entrypoint.sh" ]
CMD [ "./scripts/start.sh", "server" ]
        