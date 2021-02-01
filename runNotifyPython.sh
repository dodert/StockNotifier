#!/bin/sh
# Start/Stop Stock Notifier

case "$1" in
    start)
        echo "Starting Stock Notifier..." 
        cd /volume1/Downloads_1/pythonScripts 
        /usr/local/bin/python3 ScrappingAndNotify.py >/dev/null &
        echo "Started Stock Notifier..." 
    ;;
    stop)
        echo "Stopping Stock Notifier..."
        PID=$(ps aux | grep -v grep | grep "ScrappingAndNotify.py" | awk '{print $2}')
        echo $PID 
        kill $PID
        echo "Stopped Stock Notifier..."
    ;;
    *)
        echo "Usage: $1 {start|stop}"
    exit 1

esac
exit 0
