#!/bin/bash
cd /opt/grit/guam2/
./venv/bin/python -m uvicorn app.main:app --host 128.111.104.4 --port 8001 --reload 

