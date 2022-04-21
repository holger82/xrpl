#!/bin/bash
docker build -t xrpl .
docker run -dp 8000:80 xrpl