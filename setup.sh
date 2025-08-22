#!/bin/bash
# Setup script para MCP Trello com uv + venv

set -e

echo "🚀 Configurando MCP Trello com uv + venv..."

# Verificar se uv está instalado
if ! command -v uv &> /dev/null; then
    echo "❌ uv não encontrado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Criar venv se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python -m venv venv
fi

# Ativar venv
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências com uv (muito mais rápido que pip)
echo "⚡ Instalando dependências com uv..."
uv pip install -r requirements.txt

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "📝 Criando arquivo .env..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Configure suas credenciais do Trello no arquivo .env"
fi

echo "✅ Setup concluído!"
echo ""
echo "📋 Próximos passos:"
echo "1. Configure suas credenciais: nano .env"
echo "2. Execute o MCP: ./run_mcp_venv.sh"
echo "3. Execute API HTTP: ./run_uvicorn_venv.sh"