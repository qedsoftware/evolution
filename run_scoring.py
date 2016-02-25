#!/usr/bin/env python3

import sys
import os.path
import os
import subprocess
import json

# TODO prctl (kill on parent death)

def print_err(*objs):
    print(*objs, file=sys.stderr)

def usage():
    return "Usage: %s <scoring_directory>" % sys.argv[0]

class ParamError(Exception):
    pass

class RunParams(object):
    working_directory = None
    scoring_script = None
    user_output = None
    answer = None
    scoring_log = None
    time_limit_ms = 0

class Result(object):
    succed = None
    output = None

def read_params():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        # TODO add checks
        params = RunParams()
        params.working_directory = os.path.abspath(config['working_directory'])
        params.scoring_script = os.path.abspath(config['scoring_script'])
        params.user_output = os.path.abspath(config['user_output'])
        params.answer = os.path.abspath(config['answer'])
        params.scoring_log = os.path.abspath(config['scoring_log'])
        params.time_limit_ms = config['time_limit_ms']
        return params

def preexec():
    pass

def run(params):
    result = Result()
    args = ['python3', params.scoring_script, params.user_output,
        params.answer]
    try:
        with open(params.scoring_log, 'w') as log_file:
            completed = subprocess.run(args, timeout=params.time_limit_ms,
                preexec_fn=preexec, stdout=subprocess.PIPE, stderr=log_file)

            if (completed.returncode == 0):
                result.succed = True
                result.output = completed.stdout.decode(errors='replace')
            else:
                result.succed = False
                result.output = "Scoring script exited with code %s" % \
                    completed.returncode
    except TimeoutExpired as expired:
        result.succed = False
        result.output = "Scoring script timed out"
    return result


def main():
    try:
        if (len(sys.argv) != 2):
            raise ParamError(usage())
        scoring_directory = sys.argv[1]
        if (not os.path.isdir(scoring_directory)):
            raise ParamError(
                "Scoring directory \"%s\" doesn't exist or is not a directory."
                    % scoring_directory)
        os.chdir(scoring_directory)
        params = read_params()
        result = run(params)
        #re.match(r'^[0-9]+([.][0-9]{1,6})?$', result)
        print(result.output, end="")
        if result.succed:
            sys.exit(0)
        else:
            sys.exit(1)
    except ParamError as e:
        print_err(e)
        sys.exit(2)

if __name__ == "__main__":
    main()
