#!/usr/bin/env python3
"""Script para executar o servidor uvicorn."""

import sys
import os

# Adicionar src ao Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn

if __name__ == "__main__":
    # Executar uvicorn diretamente
    uvicorn.run(
        "mcp_trello.server:mcp",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )