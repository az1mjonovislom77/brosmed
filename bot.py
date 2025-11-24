import asyncio
import os
import re
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import aiofiles
from decouple import config

BOT_TOKEN = config('BOT_TOKEN')

CHECK_PATIENT_URL = "https://api.brosmed.uz/check-patient/"
EXPORT_ANALYSIS_URL = "https://api.brosmed.uz/export-by-phone/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_bot_files"
os.makedirs(TEMP_DIR, exist_ok=True)

user_state = {}


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone.strip())
    if digits.startswith("998") and len(digits) == 12:
        digits = digits[3:]
    if len(digits) == 9:
        return "+998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+998" + digits[3:]
    return phone


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Yangi raqam kiritish")],
            [KeyboardButton(text="Yana tahlil olish")]
        ],
        resize_keyboard=True
    )


def departments_kb(departments):
    buttons = [[KeyboardButton(text=d["title"])] for d in departments]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_state[message.chat.id] = {"step": "phone"}
    await message.answer(
        "Assalomu alaykum!\n\n"
        "Telefon raqamingizni kiriting (masalan: +998901234567):\n",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id not in user_state:
        user_state[chat_id] = {"step": "phone"}

    state = user_state[chat_id]

    if text == "Yangi raqam kiritish":
        user_state[chat_id] = {"step": "phone"}
        await message.answer("Yangi telefon raqam kiriting:", reply_markup=ReplyKeyboardRemove())
        return

    if text == "Yana tahlil olish":
        if "phone" not in state or "departments" not in state:
            await message.answer("Avval telefon raqam kiriting.")
            return
        state["step"] = "choose_department"
        await message.answer("Bo‘lim tanlang:", reply_markup=departments_kb(state["departments"]))
        return

    if state["step"] == "phone":
        clean_phone = normalize_phone(text)
        if not clean_phone.startswith("+998") or len(clean_phone) != 13:
            await message.answer("Iltimos telefon raqamni to‘g‘ri kiriting.\nMasalan: +998901234567")
            return

        state["phone"] = clean_phone
        state["step"] = "checking_patient"
        await message.answer("Tekshirilmoqda...")

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(CHECK_PATIENT_URL, json={"phone": clean_phone})
                if resp.status_code != 200:
                    await message.answer('''Ushbu raqam egasiga tegishli tahlil natijalari mavjud emas.''')
                    del state["phone"]
                    state["step"] = "phone"
                    return

                data = resp.json()
                departments = data.get("department_types", [])

                if not departments:
                    await message.answer("Bu bemorda hech qanday tahlil topilmadi.")
                    state["step"] = "phone"
                    return

                state["departments"] = departments
                state["step"] = "choose_department"

                await message.answer(
                    f"Bemor topildi!\n\nMavjud bo‘limlar:",
                    reply_markup=departments_kb(departments)
                )

        except Exception as e:
            print("Check patient xato:", e)
            await message.answer("Server bilan bog‘lanishda xatolik. Qayta urining.")
            state["step"] = "phone"
        return

    if state["step"] == "choose_department":
        selected = None
        for dept in state["departments"]:
            if dept["title"] == text:
                selected = dept
                break

        if not selected:
            await message.answer("Iltimos, ro‘yxatdan tanlang.")
            return

        state["selected_dept"] = selected
        state["step"] = "sending_files"

        await message.answer(
            f"{text} bo‘limi tanlandi.\nFayllar tayyorlanmoqda...",
            reply_markup=ReplyKeyboardRemove()
        )

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    EXPORT_ANALYSIS_URL,
                    json={
                        "phone": state["phone"],
                        "department_type_id": selected["id"]
                    }
                )

                if resp.status_code != 200:
                    await message.answer("Tahlil fayllari topilmadi yoki xatolik yuz berdi.")
                    state["step"] = "choose_department"
                    return

                files = resp.json().get("files", [])

                if not files:
                    await message.answer("Bu bo‘limda tahlil topilmadi.")
                else:
                    await message.answer(f"{len(files)} ta tahlil topildi. Yuborilmoqda...")

                    for file_info in files:
                        url = file_info["url"]
                        filename = file_info["filename"]

                        try:
                            async with httpx.AsyncClient(timeout=60) as client:
                                r = await client.get(url)
                                if r.status_code == 200:
                                    temp_path = os.path.join(TEMP_DIR, filename)
                                    async with aiofiles.open(temp_path, "wb") as f:
                                        await f.write(r.content)

                                    await message.answer_document(
                                        FSInputFile(temp_path),
                                        caption=f"{filename}"
                                    )
                                    os.remove(temp_path)
                                    await asyncio.sleep(1.2)
                        except Exception as e:
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
