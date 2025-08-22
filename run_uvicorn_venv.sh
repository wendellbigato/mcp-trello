#!/bin/bash
# Script para executar API HTTP com uvicorn usando venv

set -e

# Verificar se venv existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado. Execute ./setup.sh primeiro"
    exit 1
fi

# Ativar venv
source venv/bin/activate

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado. Configure suas credenciais do Trello"
    exit 1
fi

echo "🚀 Iniciando MCP Trello API HTTP em http://127.0.0.1:8000"
echo "📖 Documentação: http://127.0.0.1:8000/docs"
python run_uvicorn.py