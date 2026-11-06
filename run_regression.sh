#!/bin/sh
# the quick regression tests (tests/test_regression.py, about 10 seconds); these should always pass
# usage: ./run_regression.sh [-v]        (KEEP_TEST_LOGS=1 ./run_regression.sh keeps their files in tests/logs/)
cd "$(dirname "$0")" && exec python3 -m unittest tests.test_regression "$@"
