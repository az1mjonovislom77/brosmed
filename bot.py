import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import FSInputFile
import os

BOT_TOKEN = "8311992216:AAFt3Bs5fxecz1GcEtO8MfuLDooZKMkD1_0"
API_URL = "http://127.0.0.1:8000/export-by-phone/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DEPARTMENTS = {
    "1": "Qon tahlili",
    "2": "Mochevina",
    "3": "Rentgen",
    "4": "UZI"
}

user_state = {}
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    chat_id = message.chat.id
    user_state[chat_id] = {}
    await message.answer("Assalomu alaykum!\n📞 Telefon raqamingizni kiriting.\n\nMasalan: +998901234567")

@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id

    if chat_id not in user_state:
        user_state[chat_id] = {}

    if not message.text:
        await message.answer("❗ Iltimos faqat matn yuboring.")
        return

    text = message.text.strip()

    # 1) PHONE step
    if "phone" not in user_state[chat_id]:
        user_state[chat_id]["phone"] = text
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=v)] for v in DEPARTMENTS.values()],
            resize_keyboard=True
        )
        await message.answer("🔍 Bo‘limni tanlang:", reply_markup=kb)
        return

    dept_id = None
    for k, v in DEPARTMENTS.items():
        if v == text:
            dept_id = k
            break

    if dept_id is None:
        await message.answer("❌ Noto‘g‘ri bo‘lim tanlandi. Qayta urinib ko‘ring.")
        return

    user_state[chat_id]["dept_id"] = dept_id
    await message.answer("⏳ Tahlilingiz tayyorlanmoqda...")

    try:
        response = requests.post(
            API_URL,
            json={
                "phone": user_state[chat_id]["phone"],
                "department_type_id": int(dept_id)
            },
            verify=False,
            timeout=30
        )

        if response.status_code == 200:
            file_name = f"analysis_{chat_id}.docx"
            file_path = os.path.join(TEMP_DIR, file_name)
            with open(file_path, "wb") as f:
                f.write(response.content)

            doc_file = FSInputFile(file_path, filename="analysis.docx")
            await message.answer_document(doc_file, caption="📄 Sizning tahlilingiz tayyor!")
            os.remove(file_path)

        else:
            await message.answer(f"❌ Tahlil topilmadi!")

    except Exception as e:
        await message.answer(f"⚠️ Xatolik: {str(e)}")

    user_state.pop(chat_id, None)

async def main():
    print("🚀 Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot o‘chirildi.")
