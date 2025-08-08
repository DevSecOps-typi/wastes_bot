import random
import os
import csv
from telegram import Update
from telegram import ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime
from utils import log_expense
from config import CATEGORIES, random_responses
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Дарова кожаный, посчитаю твои бабки, и буду вести твой бюджет")
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()#capitalize() # Strip убирает лишнии пробелы, capitalize делает первую букву зыглавную
    if text == "/статус":
        await status(update, context)
        return
    if text == "🔙 Назад":
        context.user_data.pop("pending_category", None)
        await update.message.reply_text("Х*й с тобой, давай по новой 💸")
        return
    if text == "✅ Да":
        pending_category = context.user_data.get("pending_category")
        if pending_category:
            amount = context.user_data.get("last_amount")
            meta = CATEGORIES[pending_category]
            date = datetime.now().strftime('%d.%m.%Y %H:%M')
            username = update.message.from_user.username or "Без ника"

            log_expense(amount, pending_category, meta, date, username)

            await update.message.reply_text(
                f"Записал: {amount}₽ → {pending_category} ({meta})\n🕒 {date}"
            )
            context.user_data.pop("pending_category", None)
            context.user_data.pop("last_amount", None)

            reply_markup = ReplyKeyboardMarkup([["/статус"]], resize_keyboard=True)
            await update.message.reply_text("Жду новую сумму 💸", reply_markup=reply_markup)
            return
        amount = context.user_data.get("pending_amount")
        if amount is None:
            await update.message.reply_text(random.choice(random_responses))
            return
        context.user_data['last_amount'] = amount
        keyboard = [[cat] for cat in CATEGORIES.keys()]
        keyboard.append(["🔙 Назад"])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
        f"Учел: {amount:.2f}₽.\nКуда слил?",
        reply_markup=reply_markup
        )
        return
    try:
        amount = float(text.replace(',', '.')) # Сумма в число
        context.user_data['pending_amount'] = amount #Временно хранилищи суммы до потверждения
        keyboard = [["🔙 Назад", "✅ Да"]] #Кнопки потверждения - создает кнопки 
        # кнопки скроются после нажатия, кнопки под размер экрана подстроятся
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text( #Отправка смс
            f"Учел: {amount}₽.\nВсе верно?",
            reply_markup=reply_markup #Вывод кнопок
        )
        return
    except ValueError:
        if text == "🔙 Назад":
            context.user_data.pop("last_amount", None)
            await update.message.reply.text("Окей,х*й. Введи сумму заново 💸")
            return
        if text in CATEGORIES:
            amount = context.user_data.get("last_amount")
            if amount is None:
                await update.message.reply_text(random.choice(random_responses))        
                return
            context.user_data['pending_category'] = text
            keyboard = [["🔙 Назад", "✅ Да"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(
                f"❗Подтвердите запись: {amount:.2f}₽ → {text}",
                reply_markup=reply_markup
            )
            return
        else:
            await update.message.reply_text(random.choice(random_responses))
            return
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists("log.csv"):
        await update.message.reply_text("Нет данных о тратах в этом месяце")
        return
    now = datetime.now()
    current_month = now.strftime("%m.%Y")
    from collections import defaultdict
    category_totals = defaultdict(float)
    total_sum = 0
    must_sum = 0
    optional_sum = 0
    with open("log.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date_obj = datetime.strptime(row["Дата"],"%d.%m.%Y %H:%M")
                row_month = date_obj.strftime("%m.%Y")
                if row_month != current_month:
                    continue
            except Exception as e:
                print(f"Ошибка при разборе даты: {row['Дата']}", e)
                continue
            amount = float(row["Сумма"])
            category = row["Категория"]
            category = row["Категория"]
            meta = CATEGORIES.get(category, "необязательная") # ← напрямую из глобального словаря
            category_totals[category] += amount
            total_sum += amount
            if meta == "обязательная":
                must_sum += amount
            else:
                optional_sum += amount
    lines = [f"📊 Статистика за {current_month}:\n"]
    for cat, summ in category_totals.items():
        lines.append(f"{cat}: {summ:.2f}₽")
    lines.append("")  # Пустая строка для разделения
    lines.append(f"💰 Всего: {total_sum:.2f}₽")
    lines.append(f"✅ Обязательные: {must_sum:.2f}₽")
    lines.append(f"🌀 Необязательные: {optional_sum:.2f}₽")
    await update.message.reply_text("\n".join(lines))