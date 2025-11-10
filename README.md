# local command agent 🚀

yo so basically i got tired of clicking around for everything so i built this thing. it's like raycast but runs completely local with AI that learns your commands.

## wtf is this

- hit `cmd+shift+space` and type what u want in plain english
- local AI figures out what u mean (no cloud bs)
- runs scripts or generates new ones if needed
- remembers everything for next time

## why tho

- privacy: everything stays on ur machine
- fast af: no network calls
- gets smarter: builds up custom commands over time
- free: no subscriptions lol

## requirements

- macOS (tested on m4 pro)
- ollama installed
- python 3.10+
- node 20+

## quick start

```bash
# easy way
./setup.sh

# or manual:
# 1. install ollama models
ollama pull phi3
ollama pull qwen2.5-coder

# 2. backend
cd backend
pip3 install -r requirements.txt
python3 main.py

# 3. frontend (new terminal)
cd frontend
npm install
npm start
```

press `cmd+shift+space` to open

## how it works

1. type command in natural language
2. small model parses intent
3. checks if we got a script for that
4. if not, bigger model writes one
5. saves it and runs it
6. next time it just remembers

## commands dir

drop ur own scripts in `plugins/` and it'll learn em

## status

working on it. bugs expected. yolo.

## stack

- backend: python + fastapi
- nlu: ollama (phi3)
- codegen: ollama (qwen2.5-coder)
- rag: chromadb
- frontend: electron + react (maybe)
- db: sqlite

---

made this cuz i was bored. sue me ¯\_(ツ)_/¯
