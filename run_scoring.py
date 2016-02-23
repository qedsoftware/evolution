#!/usr/bin/env python3

import sys
import os.path

def print_err(*objs):
    print(*objs, file=sys.stderr)

def usage():
    return "Usage: %s <scoring_directory>" % sys.argv[0]

class ParamError(Exception):
    pass

class RunParams(object):
    input_dirs = {}


def run(params):
    pass

def main():
    try:
        if (len(sys.argv) != 2):
            raise ParamError(usage())
        scoring_directory = sys.argv[1]
        if (not os.path.isdir(scoring_directory)):
            raise ParamError(
                "Scoring directory \"%s\" doesn't exist or is not a directory."
                    % scoring_directory)
    except ParamError as e:
        print_err(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
