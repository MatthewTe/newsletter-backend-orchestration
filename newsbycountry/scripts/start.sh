#!/bin/sh

if [ $# -eq 0 ]; then  
    echo "Usage: start.sh [PROCESS_TYPE](server/beat/worker)"  
    exit 1  
fi  

PROCESS_TYPE=$1  

if [ "$PROCESS_TYPE" = "server" ]; then  
    if [ "$DJANGO_DEBUG" = "true" ]; then  
        python manage.py runserver 0.0.0.0:8000
    else  
        gunicorn \
            --bind 0.0.0.0:8000 \
            --workers 2 \
            --worker-class eventlet \
            --log-level DEBUG \
            --access-logfile "-" \
            --error-logfile "-" \
            newsbycountry.wsgi  
    fi  
elif [ "$PROCESS_TYPE" = "beat" ]; then
    sleep 20
    celery \
        --app newsbycountry.celery \
        beat \
        --loglevel INFO \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler  
elif [ "$PROCESS_TYPE" = "worker" ]; then  
    sleep 20
    celery \
        --app newsbycountry.celery \
        worker \
        --loglevel INFO  
fi

