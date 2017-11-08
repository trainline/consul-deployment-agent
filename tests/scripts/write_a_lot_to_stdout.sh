#!/bin/sh

for i in `seq 1 1000`; do
    seq -s ', ' 1 80
done
echo 'Finished'
