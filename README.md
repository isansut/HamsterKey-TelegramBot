# HamsterKey-TelegramBot
![image](https://github.com/isansut/HamsterKey-TelegramBot/blob/main/hamsterkey.jpg))
### saya hanya menambahkan sedikit kode supaya bisa di jalankan menggunakan bot telegram

## Tutor Install Dan Menggunakan
1. Clone the repository or download the script.
    ```sh
    git clone https://github.com/isansut/HamsterKey-TelegramBot
    ```
2. Edit Bot Token
    ```sh
    [BOT_TOKEN = 'TOKEN BOT'] ganti dengan token bot yang sudah di buat di botfather (line 23)
    ```
3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
4. Run Bot
   ```sh
   python3 keys.py
   ```
5. Open Bot Telegram Untuk pertama kali
   ```sh
   /start
   ```
   Untuk Generate Kunci
   ```sh
   /generate_key <nomor_game> <jumlah_kunci>
   ```
   
## Requirements
- Python 3.7+
- `httpx`
- `asyncio`
- `loguru`
- `telegram`


source code : https://github.com/ShafiqSadat/HamsterKeyGen
