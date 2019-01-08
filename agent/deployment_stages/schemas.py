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
        "server_script_isfile": {"type": ["string", "boolean"]},
        "tip": {"type": ["string", "boolean"]},
        "runbook": {"type": ["string", "boolean"]},
        "standalone": {"type": "boolean"},
        "aggregate": {"type": ["boolean", "string"]},
        "aggregates": {
            "type": "array",
            "items": {"type": "string"}
        },
        "ticketing_enabled": {"type": "boolean"},
        "paging_enabled": {"type": "boolean"},
        "project": {"type": "boolean"},

        "team": {"type": "string"},
        "override_notification_settings": {"type": "string"},
        "notification_email": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            }
        },
        "override_notification_email": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            }
        },
        "override_chat_channel": {
            "type": "array",
            "items": {"type": "string"}
        },

        "page": {"type": "boolean"}
    },
    "required": ["name", "interval"]
}