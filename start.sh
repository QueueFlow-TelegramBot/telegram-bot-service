#!/bin/bash
# Start Script for Application

if [ -f .env ]; then
    echo "Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
fi

source venv/bin/activate



# Flask app
###
export FLASK_APP=app.py
export FLASK_ENV=production

echo "Starting Flask service..."
gunicorn -w 4 -b 0.0.0.0:5000 app:app
###



# Non flask app
###
# python main.py
###



echo "Service started in background."
