# Chatbot CLI (Claude API)

Chatbot di terminal pakai Claude API (model `claude-haiku-5-5`). Fitur: ingat konteks percakapan, punya persona lewat system prompt, jawaban streaming, tahan error, hitung token, dan simpan riwayat chat ke JSON.

## Setup

Butuh Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
copy .env.example .env          # Windows (Mac/Linux: cp .env.example .env)
```

Isi `ANTHROPIC_API_KEY` di `.env` pakai key dari Claude Console.

## Jalankan

```bash
python chatbot.py
```

| Command | Fungsi |
|---|---|
| `/exit` | Keluar (bisa juga Ctrl+C) |
| `/reset` | Mulai obrolan baru |
| `/save` | Simpan percakapan ke `chats/` |

## Versi gratis: Ollama (model lokal)

[chatbot_ollama.py](chatbot_ollama.py) adalah versi kembaran yang jalan di laptop sendiri, tanpa API key.

1. Install Ollama dari https://ollama.com/download, lalu pastikan aplikasinya jalan
2. Download modelnya (sekitar 2GB, cukup sekali): `ollama pull qwen2.5:3b`
3. Jalankan: `python chatbot_ollama.py`
