# xrpl account overview
inspired by https://xrpl-adventure.netlify.app/ I wanted to provide an implementation that is a little more flexible regarding input and output. No focus on UI. The tool takes and account on the xrp ledger, traverses the trustlines and calculates the total value of each account line and total value in your desired fiat currency (USD, EUR,..)

# Disclaimer
* This is my very first attempt with python so I am sure there is place to improve.
* Feel free to use but dont rely on it.

The script used ripple mainnet api and coinstats api for the calculation.

# To get started:

* Clone the repo
* `cp .env.template .env`
* setup your .env file
* run the script with `python3 xrpl.py`
* Result is in `out/json_result.json`


