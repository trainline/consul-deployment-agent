#!/bin/sh

# Decrypts secret.env and passes the values as environment variables to the service
env $(tlcrypt -d < /opt/{{TTL_SERVICE_NAME_WITH_SLICE}}/secret.env) /opt/{{TTL_SERVICE_NAME_WITH_SLICE}}/{{TTL_SERVICE_EXE}}
