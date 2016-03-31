#!/bin/bash
. /home/evolution/venv/bin/activate
uwsgi --ini /home/evolution/evolution/uwsgi.conf --die-on-term
