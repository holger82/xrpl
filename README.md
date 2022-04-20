# xrpl account overview
inspired by https://xrpl-adventure.netlify.app/ I wanted to provide an implementation that is a little more flexible regarding input and output. No focus on UI. The tool takes and account on the xrp ledger, traverses the trustlines and calculates the total value of each account line and total value in your desired fiat currency (USD, EUR,..)

The application is written in python utilzing fastAPI and uvicorn as webserver.

# Disclaimer
* This is my very first attempt with python so I am sure there is place to improve.
* Feel free to use but dont rely on it.

The script used ripple mainnet api and coinstats api for the calculation.

# To get started:

* Clone the repo
* `cp .env.template .env`
* setup your .env file

# Run

For the time being logs are written directly in logs

## Docker
* Build with `docker build -t xrpl_account_info`
* Run with `docker run -dp 80:80 xrpl_account_info`

## Shell
* be sure to have  uvicorn installed (see [https://www.uvicorn.org/])
* Execute `run.sh`

# Use
* uvicorn usually starts at [http://127.0.0.1:8000]
* openAPI Docs are at [http://127.0.0.1:8000/docs]
* Take it from there.

