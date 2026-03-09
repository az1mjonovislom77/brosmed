import asyncio
import os
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import aiofiles
from decouple import config

import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = config('BOT_TOKEN')

CHECK_PATIENT_URL = "https://api.brosmed.uz/check-patient/"
EXPORT_ANALYSIS_URL = "https://api.brosmed.uz/export-by-phone/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_bot_files"
os.makedirs(TEMP_DIR, exist_ok=True)

user_state = {}


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Yangi ID kiritish")],
            [KeyboardButton(text="Yana tahlil olish")]
        ],
        resize_keyboard=True
    )


def departments_kb(departments):
    buttons = [[KeyboardButton(text=d["title"])] for d in departments]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_state[message.chat.id] = {"step": "patient_id"}
    await message.answer(
        "Assalomu alaykum!\n\n"
        "Bemor ID raqamini kiriting (masalan: 12547):",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id

    if not message.text:
        await message.answer("Iltimos, faqat raqam kiriting.")
        return

    text = message.text.strip()

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

        state["patient_id"] = int(text)
        await message.answer("Tekshirilmoqda...")

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(CHECK_PATIENT_URL, json={"patient_id": state["patient_id"]})

                logging.error(f"CHECK STATUS: {resp.status_code}")
                logging.error(f"CHECK BODY: {resp.text}")

                if resp.status_code != 200:
                    await message.answer("Bemor topilmadi.")
                    return

                data = resp.json()
                patient = data.get("patient", {})

                state["patient_name"] = patient.get("full_name", "patient")

                await message.answer(
                    f"Bemor topildi: {state['patient_name']}\n"
                    f"Tahlillar yuklanmoqda..."
                )

                export = await client.post(EXPORT_ANALYSIS_URL, json={"patient_id": state["patient_id"]})

                if export.status_code == 404:
                    await message.answer("Bu bemor uchun tahlillar topilmadi.")
                    return

                if export.status_code != 200:
                    await message.answer("Serverda xatolik yuz berdi. Keyinroq urinib ko‘ring.")
                    return

                try:
                    data = export.json()
                except Exception:
                    await message.answer("Server noto‘g‘ri javob qaytardi.")
                    return

                files = data.get("files", [])

                if not files:
                    await message.answer("Bu bemorda tahlil topilmadi.")
                    return

                await message.answer(f"{len(files)} ta tahlil topildi. Yuborilmoqda...")

                for f in files:
                    url = f["url"]
                    filename = f["filename"]

                    r = await client.get(url)
                    temp = os.path.join(TEMP_DIR, filename)

                    async with aiofiles.open(temp, "wb") as doc:
                        await doc.write(r.content)

                    await message.answer_document(FSInputFile(temp))
                    os.remove(temp)

                await message.answer("Barcha tahlillar yuborildi!", reply_markup=main_menu_kb())

        except Exception as e:
            print("Export xato:", repr(e))
            await message.answer("Server bilan bog‘lanishda xatolik.Qayta uruning")
            state["step"] = "patient_id"
        return

    if state["step"] == "choose_department":
        selected = next((d for d in state["departments"] if d["title"] == text), None)

        if not selected:
            await message.answer("Iltimos, ro‘yxatdan bo‘lim tanlang.")
            return

        state["selected_dept"] = selected
        state["step"] = "sending_files"

        await message.answer(
            f"{text} bo‘limi tanlandi.\nFayllar tayyorlanmoqda...",
            reply_markup=ReplyKeyboardRemove()
        )

        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True, verify=False) as client:
                resp = await client.post(
                    EXPORT_ANALYSIS_URL,
                    json={
                        "patient_id": state["patient_id"],
                        "department_type_id": selected["id"]
                    }
                )

                if resp.status_code != 200:
                    await message.answer("Tahlil fayllari topilmadi.")
                    state["step"] = "choose_department"
                    return

                files = resp.json().get("files", [])

                if not files:
                    await message.answer("Bu bo‘limda tahlil topilmadi.")
                else:
                    await message.answer(f"{len(files)} ta tahlil topildi. Yuborilmoqda...")

                    for file_info in files:
                        url = file_info["url"]
                        original_filename = file_info["filename"]

                        ext = os.path.splitext(original_filename)[1] or ".docx"
                        patient_name = state.get("patient_name", "patient")
                        filename = f"{patient_name}{ext}"

                        try:
                            async with httpx.AsyncClient(timeout=60) as client:
                                r = await client.get(url)
                                if r.status_code == 200:
                                    temp_path = os.path.join(TEMP_DIR, filename)
                                    async with aiofiles.open(temp_path, "wb") as f:
                                        await f.write(r.content)

                                    await message.answer_document(FSInputFile(temp_path))
                                    os.remove(temp_path)
                                    await asyncio.sleep(1.2)
                        except:
                            await message.answer(f"Fayl yuborishda xato: {filename}")

                    await message.answer("Barcha tahlillar yuborildi!", reply_markup=main_menu_kb())

        except Exception as e:
            print("Export xato:", e)
            await message.answer("Fayllar tayyorlashda xatolik yuz berdi.")

        state["step"] = "done"
        return


async def main():
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
