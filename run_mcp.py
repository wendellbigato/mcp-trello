#!/usr/bin/env python3
"""Script para executar o MCP Trello server."""

import sys
import os

# Adicionar src ao Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_trello.server import main

if __name__ == "__main__":
    main()