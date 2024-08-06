#!/bin/bash
python -m unittest discover -s .

TEST_RESULT=$?

echo $TEST_RESULT

exit $TEST_RESULT