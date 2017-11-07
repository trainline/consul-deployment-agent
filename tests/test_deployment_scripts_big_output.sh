#!/bin/sh

for i in `seq 1 10000`; do
    seq -s ', ' 1 80
done
echo 'Finished'
