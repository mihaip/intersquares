#!/bin/sh

PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python2.5 `which old_dev_appserver.py` --port=8083 app
