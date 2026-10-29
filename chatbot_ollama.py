"""Chatbot CLI pakai Ollama (model lokal, gratis): versi kembaran chatbot.py."""

import json
import os
from datetime import datetime

import httpx
import ollama

# Nggak perlu load_dotenv(): model jalan di laptop sendiri, jadi nggak ada API key.

MODEL = "qwen2.5:3b"
# Batas panjang jawaban (versi Ollama dari max_tokens).
MAX_TOKENS = 1024
# Panjang "ingatan" model (context window) dalam token. Default Ollama kecil,
# dan kalau history lebih panjang dari ini, pesan lama DIBUANG diam-diam.
# Makin besar makin banyak RAM yang kepakai.
CONTEXT_WINDOW = 8192
SYSTEM_PROMPT = """Kamu adalah 'DA' kepanjangan dari Dhanes's Assistant, AI yang santai dan suportif.
- Jawab pakai bahasa Indonesia nyantai gaya zaman sekarang tapi tetap jelas.
- Kalau ditanya soal kode, kasih penjelasan dulu baru contoh kode.
- Jawaban maksimal 5 kalimat kecuali diminta lebih panjang.
- Kalau nggak tahu, bilang nggak tahu."""
CHATS_DIR = "chats"


def chat_once(client, history):
    """Kirim system prompt + SELURUH history ke Ollama, stream jawabannya, return (teks, chunk_terakhir)."""
    # Beda dari Claude: system prompt bukan parameter terpisah, tapi pesan
    # pertama dengan role "system". Ditempel di sini (bukan disimpan di history)
    # biar /reset dan /save tetap cuma ngurusin obrolan.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    stream = client.chat(
        model=MODEL,
        messages=messages,
        stream=True,
        options={"num_predict": MAX_TOKENS, "num_ctx": CONTEXT_WINDOW},
    )

    # Ollama nggak punya get_final_message(), jadi potongan teksnya kita
    # kumpulin sendiri. Chunk terakhir (done=True) berisi info token.
    parts = []
    last_chunk = None
    for chunk in stream:
        print(chunk.message.content, end="", flush=True)
        parts.append(chunk.message.content)
        last_chunk = chunk
    print()

    return "".join(parts), last_chunk


def save_history(history):
    """Simpan percakapan ke file JSON di folder chats/."""
    os.makedirs(CHATS_DIR, exist_ok=True)
    filename = os.path.join(
        CHATS_DIR, datetime.now().strftime("chat_ollama_%Y%m%d_%H%M%S.json")
    )
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return filename


def main():
    client = ollama.Client()  # default konek ke Ollama lokal di http://localhost:11434

    history = []
    total_input = 0
    total_output = 0

    print(f"Chatbot ({MODEL}) siap! Command: /reset, /save, /exit\n")

    while True:
        try:
            user_input = input("Kamu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/reset":
            history = []
            print("(Percakapan direset)\n")
            continue
        if user_input == "/save":
            if history:
                print(f"(Disimpan ke {save_history(history)})\n")
            else:
                print("(Belum ada percakapan buat disimpan)\n")
            continue

        history.append({"role": "user", "content": user_input})
        print("Bot: ", end="", flush=True)

        try:
            reply, last_chunk = chat_once(client, history)
        except KeyboardInterrupt:
            print("\n[Dibatalin.]\n")
            history.pop()
            continue
        except (ConnectionError, httpx.ConnectError):
            # Mode biasa: library ollama ngubah error koneksi jadi ConnectionError
            # (bawaan Python). Mode stream=True: errornya lolos mentah sebagai
            # httpx.ConnectError (httpx = library HTTP yang dipakai ollama).
            print("\n[Gagal konek ke Ollama. Udah dijalanin belum? Cek ikon Ollama di taskbar.]\n")
            history.pop()
            continue
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print(f"\n[Model '{MODEL}' belum di-download. Jalanin: ollama pull {MODEL}]\n")
            else:
                print(f"\n[Error dari Ollama (status {e.status_code}): {e.error}]\n")
            history.pop()
            continue

        if not reply:
            print("[Nggak ada jawaban. Coba kalimat lain.]\n")
            history.pop()
            continue

        history.append({"role": "assistant", "content": reply})

        # Gratis, tapi token tetap dihitung: makin panjang history, makin lama
        # model "baca" prompt-nya sebelum mulai jawab.
        input_tokens = last_chunk.prompt_eval_count or 0
        output_tokens = last_chunk.eval_count or 0
        total_input += input_tokens
        total_output += output_tokens
        if last_chunk.done_reason == "length":
            print("[Jawaban kepotong karena mentok MAX_TOKENS.]")
        print(f"[token: input {input_tokens}, output {output_tokens}]\n")

    print(f"Total token sesi ini: input {total_input}, output {total_output}")
    print("see ya!")


if __name__ == "__main__":
    main()
