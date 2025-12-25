#!/bin/bash
# Stop LM Studio
lms server stop 2>/dev/null || echo "LM Studio server stopped"
