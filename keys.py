import asyncio
import os
import sys
import httpx
import random
import time
import uuid
from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from functools import partial

# Disable logging for httpx
httpx_log = logger.bind(name="httpx").level("WARNING")
logger.remove()
logger.add(sink=sys.stdout, format="<white>{time:YYYY-MM-DD HH:mm:ss}</white>"
                                   " | <level>{level: <8}</level>"
                                   " | <cyan><b>{line}</b></cyan>"
                                   " - <white><b>{message}</b></white>")
logger = logger.opt(colors=True)

# Token bot Telegram Anda
BOT_TOKEN = 'TOKEN BOT'

games = {
    1: {
        'name': 'Riding Extreme 3D',
        'appToken': 'd28721be-fd2d-4b45-869e-9f253b554e50',
        'promoId': '43e35910-c168-4634-ad4f-52fd764a843f',
    },
    2: {
        'name': 'Chain Cube 2048',
        'appToken': 'd1690a07-3780-4068-810f-9b5bbf2931b2',
        'promoId': 'b4170868-cef0-424f-8eb9-be0622e8e8e3',
    },
    3: {
        'name': 'My Clone Army',
        'appToken': '74ee0b5b-775e-4bee-974f-63e7f4d5bacb',
        'promoId': 'fe693b26-b342-4159-8808-15e3ff7f8767',
    },
    4: {
        'name': 'Train Miner',
        'appToken': '82647f43-3f87-402d-88dd-09a90025313f',
        'promoId': 'c4480ac7-e178-4973-8061-9ed5b2e17954',
    }
}

EVENTS_DELAY = 20000 / 1000  # converting milliseconds to seconds

async def load_proxies(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                proxies = [
                    {'http': f'http://{line.strip()}', 'https': f'http://{line.strip()}'}  # Format proxy
                    for line in file 
                    if line.strip()
                ]
            random.shuffle(proxies) 
            return proxies
        else:
            logger.info(f"Proxy file {file_path} not found. No proxies will be used.")
            return []
    except Exception as e:
        logger.error(f"Error reading proxy file {file_path}: {e}")
        return []


async def generate_client_id():
    timestamp = int(time.time() * 1000)
    random_numbers = ''.join(str(random.randint(0, 9)) for _ in range(19))
    return f"{timestamp}-{random_numbers}"

async def login(client_id, app_token, proxies, retries=5):
    for attempt in range(retries):
        proxy = random.choice(proxies) if proxies else None  # Gunakan proxy jika tersedia
        async with httpx.AsyncClient(proxies=proxy) as client:
            try:
                response = await client.post(
                    'https://api.gamepromo.io/promo/login-client',
                    json={'appToken': app_token, 'clientId': client_id, 'clientOrigin': 'deviceid'}
                )
                response.raise_for_status()
                data = response.json()
                return data['clientToken']
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to login (attempt {attempt + 1}/{retries}): {e.response.json()}")
            except Exception as e:
                logger.error(f"Unexpected error during login (attempt {attempt + 1}/{retries}): {e}")
        await asyncio.sleep(2)  # Delay before retrying
    logger.error("Maximum login attempts reached. Returning None.")
    return None

async def emulate_progress(client_token, promo_id, proxies):
    proxy = random.choice(proxies) if proxies else None  # Gunakan proxy jika tersedia
    async with httpx.AsyncClient(proxies=proxy) as client:
        try:
            response = await client.post(
                'https://api.gamepromo.io/promo/register-event',
                headers={'Authorization': f'Bearer {client_token}'},
                json={'promoId': promo_id, 'eventId': str(uuid.uuid4()), 'eventOrigin': 'undefined'}
            )
            response.raise_for_status()
            data = response.json()
            return data['hasCode']
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to emulate progress: {e.response.json()}")
            return False 

async def generate_key(client_token, promo_id, proxies):
    proxy = random.choice(proxies) if proxies else None  # Gunakan proxy jika tersedia
    async with httpx.AsyncClient(proxies=proxy) as client:
        try:
            response = await client.post(
                'https://api.gamepromo.io/promo/create-code',
                headers={'Authorization': f'Bearer {client_token}'},
                json={'promoId': promo_id}
            )
            response.raise_for_status()
            data = response.json()
            return data['promoCode']
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to generate key: {e.response.json()}")
            return None

async def generate_key_process(app_token, promo_id, proxies):
    client_id = await generate_client_id()
    client_token = await login(client_id, app_token, proxies)
    if not client_token:
        return None

    for _ in range(11):
        await asyncio.sleep(EVENTS_DELAY * (random.random() / 3 + 1))
        has_code = await emulate_progress(client_token, promo_id, proxies)
        if has_code:
            break

    key = await generate_key(client_token, promo_id, proxies)
    return key

async def main(game_choice, key_count, proxies=[]):  # Default proxies ke list kosong
    game = games[game_choice]
    tasks = [generate_key_process(game['appToken'], game['promoId'], proxies) for _ in range(key_count)]
    keys = await asyncio.gather(*tasks)
    return [key for key in keys if key], game['name']

async def generate_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk perintah /generate_key."""
    try:
        game_choice, key_count = map(int, context.args)

        # Kirim pesan "mohon tunggu" segera setelah perintah diterima
        await update.message.reply_text("Mohon tunggu 1-5 menit untuk mendapatkan kunci...") 

        keys, game_name = await main(game_choice, key_count)

        if keys:
            message = f"Kunci yang dihasilkan untuk {game_name}:\n" + "\n".join(keys)
            await update.message.reply_text(message) 
        else:
            message = "Tidak ada kunci yang dihasilkan."
            await update.message.reply_text(message)
    except (ValueError, IndexError):
        message = "Format perintah salah. Gunakan: /generate_key <nomor_game> <jumlah_kunci>"
        await update.message.reply_text(message)
    except Exception as e:
        message = f"Terjadi kesalahan: {e}"
        await update.message.reply_text(message)

async def generate_allkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk perintah /generate_allkey."""
    try:
        key_count_per_game = int(context.args[0])

        # Kirim pesan "mohon tunggu"
        await update.message.reply_text("Mohon tunggu, sedang menghasilkan kunci untuk semua game...")

        # Buat tugas untuk setiap game
        tasks = [main(game_choice, key_count_per_game) for game_choice in games.keys()]
        results = await asyncio.gather(*tasks)

        # Kirim hasil untuk setiap game
        for keys, game_name in results:
            if keys:
                message = f"Kunci yang dihasilkan untuk {game_name}:\n" + "\n".join(keys)
                await update.message.reply_text(message)
                for key in keys:
                    success_message = f"Result success send key: {key}"
                    await update.message.reply_text(success_message)
            else:
                message = f"Tidak ada kunci yang dihasilkan untuk {game_name}."
                await update.message.reply_text(message)

    except (ValueError, IndexError):
        message = "Format perintah salah. Gunakan: /generate_allkey <jumlah_kunci_per_game>"
        await update.message.reply_text(message)
    except Exception as e:
        message = f"Terjadi kesalahan: {e}"
        await update.message.reply_text(message)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk perintah /start."""
    game_list = "\n".join([f"{key}: {value['name']}" for key, value in games.items()])
    message = (
        "Selamat datang di SanHamsterKey!\n"
        "List Game:\n"
        f"{game_list}\n\n"
        "Format:\n"
        "/generate_key <nomor game> <jumlah kunci>\n\n"
        "Hubungi pembuat Bot @isansut\n"
        "Thanks TO :\n"
        "ShafiqSadat"
    )
    await update.message.reply_text(message)

def main_telegram() -> None:
    """Fungsi utama untuk menjalankan bot Telegram."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("generate_key", generate_key_command))
    application.add_handler(CommandHandler("generate_allkey", generate_allkey_command))  # Tambahkan handler baru

    # Memulai bot 
    application.run_polling()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        main_telegram()
    else:
        print("Select a game:")
        for key, value in games.items():
            print(f"{key}: {value['name']}")
        game_choice = int(input("Enter the game number: "))
        key_count = int(input("Enter the number of keys to generate: "))
        proxy_file = "proxy.txt"  # Tetapkan nama file proxy secara langsung

        if proxy_file:
            proxies = asyncio.run(load_proxies(proxy_file))
        else:
            proxies = []

        logger.info(f"Generating {key_count} key(s) for {games[game_choice]['name']} using {'proxies from ' + proxy_file if proxies else 'no proxies'}")
        keys, game_name = asyncio.run(main(game_choice, key_count, proxies))
        if keys:
            file_name = f"{game_name.replace(' ', '_').lower()}_keys.txt"
            logger.success(f"Generated Key(s) were successfully saved to {file_name}.")
            with open(file_name, 'a') as file:
                for key in keys:
                    formatted_key = f"{key}"
                    logger.success(formatted_key)
                    file.write(f"{formatted_key}\n")
        else:
            logger.error("No keys were generated.")

        input("Press enter to exit")
