#!/bin/bash
#
#  Run all of the tests.
#
#  Normally, you could just run `nosetests test/`, but there are some
#   odd conflicts when doing this.  The easiest fix is to just run tests
#   individually.
#
set -e
for TEST in ./test/*.py; do
    echo "Running test [$TEST]..."
    nosetests "$@" "$TEST"
    echo
done
