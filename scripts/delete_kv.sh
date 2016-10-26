#!/bin/bash

key_prefix=$1

echo "Delete all keys/values with prefix $1"
curl -v -X DELETE http://127.0.0.1:8500/v1/kv/environments/$1/?recurse
echo "Done..."
