##!/bin/bash
#
## .env
#if [ -f .env ]; then
#    export $(cat .env | grep -v '^#' | xargs)
#fi
#
## Bot run
#python bot_runner.py --token=${BOT_TOKEN}