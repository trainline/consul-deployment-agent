#!/usr/bin/env bash

if systemctl is-active test-orchestrator | grep "^active$"; then
  systemctl stop test-orchestrator
fi
