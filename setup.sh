#!/bin/bash

echo "🚀 setting up local command agent..."

# check ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ ollama not found. install from https://ollama.ai"
    exit 1
fi

echo "✓ ollama found"

# pull models
echo "pulling models (this might take a while)..."
ollama pull phi3
ollama pull qwen2.5-coder

echo "✓ models ready"

# setup backend
echo "setting up backend..."
cd backend
pip3 install -r requirements.txt

echo "✓ backend deps installed"

# setup frontend
echo "setting up frontend..."
cd ../frontend
npm install

echo "✓ frontend deps installed"

echo ""
echo "🎉 setup complete!"
echo ""
echo "to start:"
echo "  1. cd backend && python3 main.py"
echo "  2. cd frontend && npm start"
echo ""
echo "hotkey: cmd+shift+space"
