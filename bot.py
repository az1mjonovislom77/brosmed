import asyncio
import os
import re
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import aiofiles

BOT_TOKEN = "8311992216:AAFt3Bs5fxecz1GcEtO8MfuLDooZKMkD1_0"
API_URL = "http://127.0.0.1:8000/export-by-phone/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DEPARTMENTS = {
    "1": "Analiz natijasini olish"
}

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

user_state = {}


def get_department_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=v)] for v in DEPARTMENTS.values()],
        resize_keyboard=True
    )


def get_new_number_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Yangi raqam uchun analiz")],
                  [KeyboardButton(text="🔄 Yana tahlil olish")]],
        resize_keyboard=True
    )


def is_valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"\+998\d{9}", phone))


async def check_phone_exists(phone: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(API_URL, json={"phone": phone, "department_type_id": 1})
            return response.status_code == 200
    except Exception as e:
        print("Xatolik phone tekshirishda:", e)
        return False


@dp.message(Command("start"))
async def start(message: types.Message):
    chat_id = message.chat.id
    user_state[chat_id] = {"step": "phone"}
    await message.answer(
        "Assalomu alaykum!\n📞 Telefon raqamingizni kiriting.\nMasalan: +998901234567",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id not in user_state:
        user_state[chat_id] = {"step": "phone"}

    state = user_state[chat_id]

    if text == "📱 Yangi raqam uchun analiz":
        state["step"] = "phone"
        await message.answer("📞 Iltimos yangi telefon raqam kiriting:", reply_markup=ReplyKeyboardRemove())
        return

    if text == "🔄 Yana tahlil olish":
        if "phone" not in state:
            state["step"] = "phone"
            await message.answer("📞 Telefon raqamingizni kiriting:", reply_markup=ReplyKeyboardRemove())
        else:
            state["step"] = "department"
            kb = get_department_keyboard()
            await message.answer("🔍 Bo‘limni tanlang:", reply_markup=kb)
        return

    if state.get("step") == "phone":
        if not is_valid_phone(text):
            await message.answer("❌ Noto‘g‘ri telefon raqam format. Iltimos +998XXXXXXXXX formatida kiriting.")
            return

        exists = await check_phone_exists(text)
        if not exists:
            await message.answer("❌ Ushbu telefon raqam bazada topilmadi. Iltimos boshqa raqam kiriting.")
            return

        state["phone"] = text
        state["step"] = "department"
        kb = get_department_keyboard()
        await message.answer("🔍 Bo‘limni tanlang:", reply_markup=kb)
        return

    if state.get("step") == "department":
        dept_id = None
        for k, v in DEPARTMENTS.items():
            if v == text:
                dept_id = k
                break

        if dept_id is None:
            await message.answer("❌ Noto‘g‘ri bo‘lim tanlandi. Qayta urinib ko‘ring.")
            return

        state["dept_id"] = dept_id
        state["step"] = "processing"
        await message.answer("⏳ Tahlilingiz tayyorlanmoqda...", reply_markup=ReplyKeyboardRemove())

        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                response = await client.post(
                    API_URL,
                    json={"phone": state["phone"], "department_type_id": int(dept_id)}
                )
                if response.status_code == 200:
                    file_name = f"analysis_{chat_id}.docx"
                    file_path = os.path.join(TEMP_DIR, file_name)
                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(response.content)
                    doc_file = FSInputFile(file_path, filename="analysis.docx")
                    await message.answer_document(doc_file, caption="📄 Sizning tahlilingiz tayyor!")
                    os.remove(file_path)
                else:
                    await message.answer("❌ Tahlil topilmadi!")
        except Exception as e:
            await message.answer(f"⚠️ Xatolik yuz berdi: {str(e)}")

        state["step"] = "ready"
        kb = get_new_number_keyboard()
        await message.answer("🔄 Yana boshqa raqam yoki analiz olish mumkin:", reply_markup=kb)


async def main():
    print("🚀 Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot o‘chirildi.")
