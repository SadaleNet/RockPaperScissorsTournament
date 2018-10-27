# Use an official Python runtime as a parent image
FROM python:3.7-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /tmp
COPY requirements.txt /tmp

# Install any needed packages
RUN apk update
RUN apk add zlib-dev jpeg-dev freetype-dev gcc musl-dev
RUN pip install --trusted-host pypi.python.org -r /tmp/requirements.txt

# Copy the data
COPY app .

# Define volume for storing images
VOLUME ["/app/data"]

# Make port 80 available to the world outside this container
EXPOSE 80

# Used for docker to detect if the container is healthy
HEALTHCHECK --timeout=5s CMD wget -O /dev/null http://localhost || exit 1

# Run app.py when the container launches
CMD ["/bin/sh", "start.sh"]

# gunicorn -w 1 -b 0.0.0.0:80 rps:app

#docker run -p 8000:80 -e "RPS_EVENT_TITLE=Test Event" -e "RPS_START_TIME=$(date -d '2018-10-22 19:50:00' +%s)" -e "RPS_END_TIME=$(date -d '2018-10-22 19:55:00' +%s)" -e "RPS_CERT_NAME_X=400" -e "RPS_CERT_NAME_Y=610" --mount type=bind,source="$(pwd)"/data,target=/app/data -it rps sh

#docker run -p 8000:80 -e "RPS_EVENT_TITLE=Test Event" -e "RPS_START_TIME=$(date -d '2018-10-22 19:50:00' +%s)" -e "RPS_END_TIME=$(date -d '2018-10-22 19:55:00' +%s)" -e "RPS_CERT_NAME_X=400" -e "RPS_CERT_NAME_Y=610" --mount type=bind,source="$(pwd)"/app,target=/app --mount type=bind,source="$(pwd)"/app/data,target=/app/data -it rps sh
