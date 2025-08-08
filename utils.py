import csv
import os
def log_expense(amount, category, meta, date, username):
    print("📥 log_expense вызвана")
    print("Данные:", amount, category, meta, date)
#os.path.isfile() — проверяет, существует ли файл
    file_exists = os.path.isfile("log.csv")
    with open("log.csv", "a", newline ="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Дата", "Сумма", "Категория", "Тип", "Пользователь"])
        writer.writerow([date, amount, category, meta, username])