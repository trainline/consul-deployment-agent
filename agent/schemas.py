# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

SensuHealthCheckSchema = {
    "$schema": "http://json-schema.org/schema#",

    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "interval": {"type": "number"},
        "realert_every": {"type": "number"},
        "timeout": {"type": "number"},
        "occurrences": {"type": "number"},
        "refresh": {"type": "number"},

        "team": {"type": ["string", "boolean"]},
        "tip": {"type": ["string", "boolean"]},
        "runbook": {"type": ["string", "boolean"]},
        "notification_email": {"type": ["string", "boolean", "array"]},

        "standalone": {"type": "boolean"},
        "aggregate": {"type": "boolean"},
        "ticket": {"type": "boolean"},
        "project": {"type": "boolean"},
        "slack_channel": {"type": "string"},
        "page": {"type": "boolean"}
    },
    "required": ["name", "interval"]
}