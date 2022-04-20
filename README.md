# xrpl account overview
Inspired by https://xrpl-adventure.netlify.app/ I wanted to provide an implementation that is a little more flexible regarding input and output. No focus on UI. From there a small API was written which takes an account id and a target currency. It then checks the account and all baselines with a positive The tool takes and account on the xrp ledger, traverses the trustlines and calculates the total value of each account line and total value in your desired fiat currency (USD, EUR,..)

The application is written in python utilzing fastAPI and uvicorn as webserver.

# Disclaimer
* This is my very first attempt with python so I am sure there is place to improve.
* Feel free to use but dont rely on it.

Under the hood we use ripple mainnet api and coinstats api for the calculations.

# To get started:

* Clone the repo
* `cp .env.template .env`
* setup your .env file

## Docker
* Build with `docker build -t xrpl`
* Run with `docker run -dp 8000:80 xrpl` to start at [http://127.0.0.1:8000]

## Shell
* be sure to have  uvicorn installed (see [https://www.uvicorn.org/])
* Execute `run.sh`
* uvicorn usually starts at [http://127.0.0.1:8000]

## Use
* openAPI Docs are at [http://127.0.0.1:8000/docs]
* Take it from there and enjoy.
