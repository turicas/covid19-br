#!/bin/bash

gunicorn web.app:app --bind=0.0.0.0:5000 --workers=4 --log-file -
