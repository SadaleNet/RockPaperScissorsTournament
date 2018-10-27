# Rock Paper Scissors Tournament Event Website

A website for hosting Asynchronous Rock Paper Sccisors Tournaments.

This website is based on the an annual event of Rock Paper Scissors.

Live demo (Too bad! You can't join because the event had ended): [Website of International Asynchronous Rock Paper Scissors Tournament 2018](https://rps2018.sadale.net/)

## Features

* Dockerized - Deployable anywhere
* Participants can only join during the event period
* Captcha to prevent robots from joining
* Certificate are issued to all participants

## How to Deploy?

```
git clone https://github.com/SadaleNet/RockPaperScissorsTournament.git
cd RockPaperScissorsTournament
docker build -t rps -f Dockerfile .
mkdir data
docker volume 
# Command for production
docker run -d -p 8000:80 -e "RPS_EVENT_TITLE=Foo Bar RPS Event" --mount type=volume,source=rps-datavol,target=/app/data rps
# Commands below are for development
docker run -d -p 8000:80 -e "RPS_EVENT_TITLE=Foo Bar RPS Event" --mount type=bind,source="$(pwd)"/data,target=/app/data rps
# View the event's website on http://localhost:8000
# Modify the python files and certificates as you wish
kill -HUP $(ps -fax | grep -v grep | grep gunicorn | head -n 1 | awk '{$1=$1};1' | cut -d' ' -f1) #Reload the python files and assets without restarting the container. This line is only guaranteed to work if there's no other gunicorn instances
```

## Running Automated Testcases

```
git clone https://github.com/SadaleNet/RockPaperScissorsTournament.git
cd RockPaperScissorsTournament
docker build -t rps -f Dockerfile-debug .
docker run -it rps-debug py.test --verbose ./test_captcha.py ./test_rps.py
```


## Parameters (Settable with environment variables)

* RPS_EVENT_TITLE - Title of the event. The default is `International Asynchronous Rock Paper Scissors Tournament`
* RPS_START_TIME - UTC timestamp of the start of the event. The default is current UTC timestamp.
* RPS_END_TIME - UTC timestamp of the end of the event. If this is before RPS_START_TIME, the behavior is undefined. The default the UTC timestamp after 24 hours of current time
* RPS_CERT_NAME_X - Center X position of the name to be written on the .png of the certificate. Unit in pixels. The default is ```744```, which is the center of the default certificate image
* RPS_CERT_NAME_Y - Center Y position of the name to be written on the .png of the certificate. Unit in pixels. The default is ```1060```, which is the center of the default certificate image

## Known Issues

* Generating the certificate is slooow because lacking of caching.
* All of the automated test cases are passed. However, some warning are generated. Those warning are the issue of Flask itself, which is irrelevant to the code in this project.

## Stack Used

Docker, Python, Flask. And also Jenkins (not uploaded to this repo)
