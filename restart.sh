#!/bin/bash
# Restart TinyProgrammer

cd "$(dirname "$0")"
./stop.sh
sleep 2
./start.sh
