# Weekend Project: Chatbot CLI pakai Claude API

> **Target:** dalam 1 weekend (±8–10 jam), lu punya chatbot di terminal yang bisa ngobrol, ingat percakapan, punya "kepribadian", jawabannya muncul real-time (streaming), tahan error, dan bisa nyimpen riwayat chat.
>
> **Aturan main:** coba tulis sendiri dulu tiap langkah. Kode referensi lengkap ada di bagian paling bawah (dilipat), buka cuma kalau udah mentok ≥ 20 menit.

---

## Yang bakal lu pelajari

| Skill | Nyambung ke materi |
|---|---|
| Virtual environment & pip | Corey Schafer: *Pip*, *Virtual Environments* |
| Nyimpen API key dengan aman (`.env`) | Praktik standar AI engineer |
| Memanggil API LLM | Fase 2 roadmap (LLM lewat API) |
| Konsep **"API itu stateless"** (riwayat chat dikirim ulang tiap request) | Dasar semua chatbot & RAG |
| System prompt | Prompt engineering |
| Streaming | Corey Schafer: *Generators* (konsepnya mirip) |
| Error handling | Corey Schafer: *Try/Except* |
| Simpan ke JSON | Corey Schafer: *JSON module*, *File Objects* |
| Menghitung token | Ngerti biaya LLM |

---

## Prasyarat

- **Python 3.10 atau lebih baru** (SDK Anthropic butuh minimal 3.10). Cek: `python --version`
- Code editor (VS Code oke)
- Akun di **Claude Console** buat dapat API key

> ⚠️ **Soal biaya:** API Claude itu **bayar per token**, terpisah dari langganan Claude.ai (Free/Pro). Cek harga terbaru di halaman pricing resmi, dan atur batas pengeluaran di Console kalau tersedia. Project ini pakai model paling hemat (Haiku), jadi biaya buat latihan biasanya kecil, tapi tetap pantau.

---

## Struktur folder akhir

```
chatbot-claude/
├── .venv/            # virtual environment (JANGAN di-commit)
├── .env              # API key (JANGAN di-commit)
├── .gitignore
├── requirements.txt
├── chatbot.py
└── chats/            # hasil /save (dibuat otomatis)
```

---

# HARI 1: Bikin chatbot-nya jalan

## Step 0: Ambil API key (15 menit)

1. Login ke Claude Console (console.anthropic.com)
2. Buka menu **API Keys**, lalu bikin key baru
3. Salin key-nya. **Key cuma ditampilkan sekali**, simpan baik-baik.

> 🔒 API key = password. Jangan pernah ditaruh langsung di kode, di-screenshot, atau di-push ke GitHub. Kalau bocor, langsung hapus key itu di Console dan bikin yang baru.

## Step 1: Setup project (30 menit)

```bash
mkdir chatbot-claude
cd chatbot-claude

# bikin & aktifkan virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# install library
pip install anthropic python-dotenv
pip freeze > requirements.txt
```

Bikin file **`.env`**:
```
ANTHROPIC_API_KEY=sk-ant-isi-key-lu-di-sini
```

Bikin file **`.gitignore`**:
```
.venv/
.env
chats/
__pycache__/
```

Terus `git init`. Kebiasaan bagus: commit tiap step selesai.

✅ **Cek:** `pip list` harus menampilkan `anthropic` dan `python-dotenv`.

## Step 2: "Hello, Claude" (30 menit)

Bikin `chatbot.py` dan coba panggil API sekali:

```python
import anthropic
from dotenv import load_dotenv

load_dotenv()  # baca isi .env ke environment variable

client = anthropic.Anthropic()  # otomatis baca ANTHROPIC_API_KEY

MODEL = "claude-haiku-5-5"

message = client.messages.create(
    model=MODEL,
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Halo Claude! Jelasin apa itu API dalam 2 kalimat."}
    ],
)

print(message.content[0].text)
```

Jalankan: `python chatbot.py`

✅ **Cek:** muncul jawaban dari Claude.

🧪 **Eksperimen kecil:**
- `print(message)`: liat struktur lengkap respons-nya. Ada `content`, `usage`, `stop_reason`, dll.
- Ganti `max_tokens` jadi `20`. Apa yang terjadi sama jawabannya? Liat juga nilai `stop_reason`.

## Step 3: Loop chat + memori (1–2 jam) ⭐ *konsep paling penting*

**Tantangan:** bikin loop `while True` yang:
1. Minta input user
2. Kirim ke Claude
3. Print jawabannya
4. Ulang

Coba dulu yang naif, kirim **cuma pesan terakhir**. Terus tes:
```
Kamu: Nama gw Budi
Bot: ...
Kamu: Nama gw siapa?
```

Claude bakal **lupa**. Kenapa? Karena **API itu stateless**: tiap request berdiri sendiri, Claude nggak "ingat" request sebelumnya.

**Solusinya:** simpan semua percakapan di list `history`, dan kirim **seluruh** list itu tiap request:

```python
history = [
    {"role": "user", "content": "Nama gw Budi"},
    {"role": "assistant", "content": "Halo Budi! ..."},
    {"role": "user", "content": "Nama gw siapa?"},
]
```

💡 **Hint:**
- Sebelum kirim: `history.append({"role": "user", "content": user_input})`
- Setelah dapat jawaban: `history.append({"role": "assistant", "content": reply})`
- Urutan role harus selang-seling user → assistant → user → ...

✅ **Cek:** chatbot bisa ingat nama lu di giliran berikutnya.

🤔 **Pikirin:** kalau ngobrol 100 giliran, history-nya makin panjang. Apa dampaknya ke biaya dan kecepatan? (Jawabannya bakal kelihatan di Step 7.)

## Step 4: Kasih kepribadian lewat system prompt (30 menit)

Tambahin parameter `system` di `messages.create`:

```python
SYSTEM_PROMPT = """Kamu adalah 'Kak Budi', mentor coding yang santai dan suportif.
- Jawab pakai bahasa Indonesia gaul tapi tetap jelas.
- Kalau ditanya soal kode, kasih penjelasan dulu baru contoh kode.
- Jawaban maksimal 5 kalimat kecuali diminta lebih panjang.
- Kalau nggak tahu, bilang nggak tahu."""
```

```python
message = client.messages.create(
    model=MODEL,
    max_tokens=1024,
    system=SYSTEM_PROMPT,
    messages=history,
)
```

🧪 **Eksperimen:** bikin 3 persona berbeda (guru matematika galak, teman curhat, penjual bakso yang jago Python). Liat seberapa besar pengaruh system prompt ke gaya jawaban.

---

# HARI 2: Bikin chatbot-nya "proper"

## Step 5: Streaming (1 jam)

Sekarang jawaban baru muncul setelah selesai semua. Bikin muncul **kata per kata** kayak di Claude.ai:

```python
with client.messages.stream(
    model=MODEL,
    max_tokens=1024,
    system=SYSTEM_PROMPT,
    messages=history,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()
    final_message = stream.get_final_message()
```

💡 **Hint:**
- `stream.text_stream` itu iterator yang menghasilkan potongan teks satu per satu. Mirip generator yang lu pelajari dari Corey.
- `get_final_message()` mengembalikan pesan utuh. Teks lengkapnya ambil dari situ buat dimasukkan ke `history`.

✅ **Cek:** teks muncul bertahap, bukan sekaligus.

## Step 6: Error handling + command (1–1,5 jam)

**Tes dulu biar tahu error-nya kayak apa:**
- Matikan WiFi, lalu kirim pesan
- Ubah API key di `.env` jadi asal-asalan
- Ganti `MODEL` jadi nama ngawur

Program bakal crash. Bungkus pemanggilan API pakai `try/except`:

```python
try:
    ...  # panggil API
except anthropic.APITimeoutError:
    print("Kelamaan nunggu respons. Coba lagi.")
except anthropic.APIConnectionError:
    print("Gagal konek. Cek internet lu.")
except anthropic.RateLimitError:
    print("Kebanyakan request. Tunggu sebentar.")
except anthropic.APIStatusError as e:
    print(f"Error dari API (status {e.status_code}): {e.message}")
```

> ⚠️ **Jebakan:** kalau request gagal, pesan user terakhir udah terlanjur masuk `history`. Hapus lagi pakai `history.pop()` biar urutan role-nya tetap rapi.

**Tambahin command:**

| Command | Fungsi |
|---|---|
| `/exit` | Keluar |
| `/reset` | Kosongkan `history` (mulai obrolan baru) |
| `/save` | Simpan percakapan ke file JSON (Step 8) |

Bonus: tangkap `Ctrl+C` (`KeyboardInterrupt`) biar keluarnya rapi, nggak muncul traceback.

## Step 7: Hitung token (30 menit)

Tiap respons punya info pemakaian token:

```python
final_message.usage.input_tokens   # token yang lu kirim (termasuk SELURUH history + system prompt)
final_message.usage.output_tokens  # token yang dihasilkan Claude
```

Print setelah tiap jawaban, plus total di akhir sesi.

🧪 **Eksperimen:** ngobrol 10 giliran, terus perhatikan `input_tokens`. Angkanya **naik terus**, kan? Itu bukti nyata konsep "stateless" dari Step 3. Inilah alasan chatbot sungguhan perlu strategi kayak memotong history lama atau meringkasnya.

## Step 8: Simpan riwayat chat ke JSON (30 menit)

Implementasikan `/save`:

```python
import json
import os
from datetime import datetime

os.makedirs("chats", exist_ok=True)
filename = datetime.now().strftime("chats/chat_%Y%m%d_%H%M%S.json")
with open(filename, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
```

💡 `ensure_ascii=False` biar karakter non-ASCII (emoji, dll.) tetap kebaca, nggak berubah jadi `\uXXXX`.

---

## ✅ Checklist "Done"

- [ ] API key aman di `.env` dan **nggak ikut ke-commit** (cek `git status`)
- [ ] Chatbot ingat konteks percakapan
- [ ] Punya persona lewat system prompt
- [ ] Jawaban streaming
- [ ] Nggak crash pas internet mati atau API key salah
- [ ] `/exit`, `/reset`, `/save` jalan
- [ ] Token per giliran dan total sesi ditampilkan
- [ ] Ada `README.md` singkat + di-push ke GitHub

## 🧠 Tes paham (jawab tanpa liat kode)

1. Kenapa chatbot lupa nama lu di versi naif Step 3?
2. Kenapa `input_tokens` naik terus selama ngobrol? Apa dampaknya ke biaya?
3. Apa bedanya pesan di `system` dengan pesan `user`?
4. Kenapa API key nggak boleh ditulis langsung di `chatbot.py`?
5. Kenapa perlu `history.pop()` waktu request gagal?

Kalau bisa jawab semua, lu udah paham fondasi yang dipakai di **semua** aplikasi LLM, termasuk RAG dan agent nanti.

---

## 🚀 Bonus (kalau masih semangat)

1. **Batasi history:** cuma kirim N pesan terakhir biar biaya nggak membengkak.
2. **Load chat lama:** command `/load <nama_file>` buat melanjutkan percakapan yang disimpan.
3. **Ganti model:** coba model Claude yang lebih besar, bandingkan kualitas jawaban dan token-nya.
4. **Bikin jadi API:** bungkus pakai **FastAPI** (endpoint `POST /chat`). Ini latihan langsung buat Fase 0 roadmap lu.
5. **Kasih UI web sederhana** pakai Streamlit.

---

## 🛠️ Troubleshooting

| Masalah | Kemungkinan penyebab |
|---|---|
| `AuthenticationError` / status 401 | API key salah, atau `.env` nggak kebaca (cek `load_dotenv()` dipanggil sebelum `Anthropic()`) |
| `ModuleNotFoundError: anthropic` | venv belum diaktifkan, atau install di environment lain |
| Status 404 / model not found | Nama model salah ketik. Cek daftar model di dokumentasi resmi |
| Jawaban kepotong | `max_tokens` terlalu kecil |
| Error soal urutan role | Ada dua pesan `user` berturut-turut di `history` (lupa `pop()` waktu error) |

---

## 📚 Referensi

- Dokumentasi Python SDK resmi: https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python
- Prompt engineering (Anthropic): https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
- Anthropic Academy, kursus *Building with the Claude API*: kelanjutan alami setelah project ini

---

<details>
<summary><b>📄 Kode referensi lengkap (buka kalau udah mentok!)</b></summary>

```python
"""Chatbot CLI pakai Claude API: weekend project."""

import json
import os
from datetime import datetime

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 1024
SYSTEM_PROMPT = """Kamu adalah 'Kak Budi', mentor coding yang santai dan suportif.
- Jawab pakai bahasa Indonesia gaul tapi tetap jelas.
- Kalau ditanya soal kode, kasih penjelasan dulu baru contoh kode.
- Jawaban maksimal 5 kalimat kecuali diminta lebih panjang.
- Kalau nggak tahu, bilang nggak tahu."""

client = anthropic.Anthropic()  # baca ANTHROPIC_API_KEY dari environment


def chat_once(history):
    """Kirim seluruh history ke Claude, stream jawabannya, return (teks, usage)."""
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=history,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        print()
        final_message = stream.get_final_message()

    reply = "".join(
        block.text for block in final_message.content if block.type == "text"
    )
    return reply, final_message.usage


def save_history(history):
    """Simpan percakapan ke file JSON di folder chats/."""
    os.makedirs("chats", exist_ok=True)
    filename = datetime.now().strftime("chats/chat_%Y%m%d_%H%M%S.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return filename


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY belum diset. Cek file .env lu.")
        return

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

        try:
            reply, usage = chat_once(history)
        except anthropic.APITimeoutError:
            print("\n[Kelamaan nunggu respons. Coba lagi.]\n")
            history.pop()
            continue
        except anthropic.APIConnectionError:
            print("\n[Gagal konek. Cek internet lu.]\n")
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

        history.append({"role": "assistant", "content": reply})
        total_input += usage.input_tokens
        total_output += usage.output_tokens
        print(f"[token: input {usage.input_tokens}, output {usage.output_tokens}]\n")

    print(f"Total token sesi ini: input {total_input}, output {total_output}")
    print("Dadah! 👋")


if __name__ == "__main__":
    main()
```

</details>
