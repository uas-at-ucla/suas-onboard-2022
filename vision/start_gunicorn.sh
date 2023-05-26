#!/bin/sh
if [ $DUMMY ]
then
    echo "Running dummy app..."
    gunicorn dummy:app -w 1 -b 0.0.0.0:8003 --access-logfile -
else
    gunicorn main:app -w 1 -b 0.0.0.0:8003 --access-logfile -
fi

exec "$@"
