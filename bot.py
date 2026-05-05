import asyncio
import os
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from decouple import config
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = config('BOT_TOKEN')

CHECK_PATIENT_URL = "https://api.brosmed.uz/check-patient/"
EXPORT_ANALYSIS_URL = "https://api.brosmed.uz/export-by-phone/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_state = {}


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Yangi ID kiritish")],
            [KeyboardButton(text="Yana tahlil olish")]
        ],
        resize_keyboard=True
    )


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_state[message.chat.id] = {"step": "patient_id"}
    await message.answer(
        "Assalomu alaykum!\n\n"
        "Bemor ID raqamini kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    if chat_id not in user_state:
        user_state[chat_id] = {"step": "patient_id"}

    state = user_state[chat_id]

    if text == "Yangi ID kiritish":
        user_state[chat_id] = {"step": "patient_id"}
        await message.answer("Yangi bemor ID kiriting:", reply_markup=ReplyKeyboardRemove())
        return

    if state["step"] == "patient_id":

        if not text.isdigit():
            await message.answer("ID faqat raqamlardan iborat bo‘lishi kerak.")
            return

        patient_id = int(text)
        state["patient_id"] = patient_id

        await message.answer("Tekshirilmoqda...")

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(CHECK_PATIENT_URL, json={"patient_id": patient_id})

                if resp.status_code != 200:
                    await message.answer("Bemor topilmadi.")
                    return

                data = resp.json()
                patient = data.get("patient", {})

                patient_name = patient.get("full_name") or "patient"
                patient_name = patient_name.replace(" ", "_")

                state["patient_name"] = patient_name

                await message.answer(
                    f"Bemor topildi: {patient_name}\n"
                    f"Tahlillar yuklanmoqda..."
                )

                export = await client.post(EXPORT_ANALYSIS_URL, json={"patient_id": patient_id})

                if export.status_code != 200:
                    await message.answer("Server xatoligi.")
                    return

                data = export.json()
                files = data.get("files", [])

                if not files:
                    await message.answer("Tahlil topilmadi.")
                    return

                await message.answer(f"{len(files)} ta tahlil topildi. Yuborilmoqda...")

                for index, f in enumerate(files, start=1):
                    url = f["url"]
                    original_filename = f["filename"]

                    ext = os.path.splitext(original_filename)[1] or ".pdf"
                    filename = f"{patient_name}_{index}{ext}"
                    print(url)
                    r = await client.get(url)

                    if r.status_code != 200:
                        await message.answer("Faylni yuklab bo‘lmadi.")
                        continue

                    file = BufferedInputFile(r.content, filename=filename)
                    await message.answer_document(file)

                    await asyncio.sleep(0.5)

                await message.answer(
                    "Barcha tahlillar yuborildi!",
                    reply_markup=main_menu_kb()
                )

        except Exception as e:
            logging.exception(e)
            await message.answer("Server bilan bog‘lanishda xatolik.")

        state["step"] = "patient_id"


async def main():
    print("Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
