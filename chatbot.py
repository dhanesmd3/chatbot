"""Chatbot CLI pakai Claude API: weekend project."""

import json
import os
from datetime import datetime

import anthropic
from dotenv import load_dotenv

# Baca isi .env ke environment variable. HARUS sebelum bikin client.
load_dotenv()

MODEL = "claude-haiku-5-5"
# Haiku 5.5 "mikir" dulu (thinking) sebelum jawab, dan token mikirnya ikut
# dihitung ke max_tokens. Kalau terlalu kecil, jawabannya bisa kepotong.
MAX_TOKENS = 4096
# Effort ngatur seberapa keras model mikir. Buat ngobrol santai, "low" cukup:
# lebih cepat dan lebih hemat token.
EFFORT = "low"
SYSTEM_PROMPT = """Kamu adalah 'DA' kepanjangan dari Dhanes's Assistant, AI yang santai dan suportif.
- Jawab pakai bahasa Indonesia nyantai gaya zaman sekarang tapi tetap jelas.
- Kalau ditanya soal kode, kasih penjelasan dulu baru contoh kode.
- Jawaban maksimal 5 kalimat kecuali diminta lebih panjang.
- Kalau nggak tahu, bilang nggak tahu."""
CHATS_DIR = "chats"


def chat_once(client, history):
    """Kirim SELURUH history ke Claude, stream jawabannya, return (teks, usage, stop_reason)."""
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=history,
        output_config={"effort": EFFORT},
    ) as stream:
        # text_stream itu iterator: tiap potongan teks langsung di-print begitu datang.
        for text in stream.text_stream:
            print(text, end="", flush=True)
        print()
        final_message = stream.get_final_message()

    # Respons bisa berisi beberapa blok (misal blok "thinking" + blok "text").
    # Ambil berdasarkan type, jangan asal content[0].
    reply = "".join(
        block.text for block in final_message.content if block.type == "text"
    )
    return reply, final_message.usage, final_message.stop_reason


def save_history(history):
    """Simpan percakapan ke file JSON di folder chats/."""
    os.makedirs(CHATS_DIR, exist_ok=True)
    filename = os.path.join(
        CHATS_DIR, datetime.now().strftime("chat_%Y%m%d_%H%M%S.json")
    )
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return filename


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY belum diset. Cek file .env lu.")
        return

    client = anthropic.Anthropic()  # otomatis baca ANTHROPIC_API_KEY dari environment

    history = []
    total_input = 0
    total_output = 0

    print("Chatbot siap! Command: /reset, /save, /exit\n")

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

        # Urutan except penting: yang paling spesifik dulu. APITimeoutError itu
        # turunan APIConnectionError, dan AuthenticationError/NotFoundError/
        # RateLimitError itu turunan APIStatusError.
        try:
            reply, usage, stop_reason = chat_once(client, history)
        except KeyboardInterrupt:
            print("\n[Dibatalin.]\n")
            history.pop()
            continue
        except anthropic.APITimeoutError:
            print("\n[Kelamaan nunggu respons. Coba lagi.]\n")
            history.pop()
            continue
        except anthropic.APIConnectionError:
            print("\n[Gagal konek. Cek internet lu.]\n")
            history.pop()
            continue
        except anthropic.AuthenticationError:
            print("\n[API key salah atau nggak valid. Cek file .env lu.]\n")
            history.pop()
            continue
        except anthropic.NotFoundError:
            print(f"\n[Model '{MODEL}' nggak ketemu. Cek nama modelnya.]\n")
            history.pop()
            continue
        except anthropic.RateLimitError:
            print("\n[Kebanyakan request. Tunggu sebentar lalu coba lagi.]\n")
            history.pop()
            continue
        except anthropic.APIStatusError as e:
            print(f"\n[Error dari API (status {e.status_code}): {e.message}]\n")
            history.pop()
            continue

        # Token tetap kepakai (dan dibayar) walaupun jawabannya kosong.
        total_input += usage.input_tokens
        total_output += usage.output_tokens

        if not reply:
            # Misal model menolak (stop_reason "refusal") atau token habis buat mikir.
            # Jangan masukin jawaban kosong ke history, nanti request berikutnya error.
            print(f"[Nggak ada jawaban (stop_reason: {stop_reason}). Coba kalimat lain.]\n")
            history.pop()
            continue

        history.append({"role": "assistant", "content": reply})
        if stop_reason == "max_tokens":
            print("[Jawaban kepotong karena mentok MAX_TOKENS.]")
        print(f"[token: input {usage.input_tokens}, output {usage.output_tokens}]\n")

    print(f"Total token sesi ini: input {total_input}, output {total_output}")
    print("see ya!")


if __name__ == "__main__":
    main()
