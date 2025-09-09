import tkinter as tk
from tkinter import messagebox, scrolledtext
from collections import defaultdict
import copy
import random
from PIL import Image, ImageTk
import os

# Рецепты крафта: ключ - уровень целевого шара, значение - словарь {компонент: количество}
recipes = {
    2: {1: 4},  # Шар 2 ур. = 4 шара 1 ур.
    3: {1: 2, 2: 2},  # Шар 3 ур. = 2 шара 1 ур. + 2 шара 2 ур.
    4: {1: 1, 2: 1, 3: 2},  # Шар 4 ур. = 1 шар 1 ур. + 1 шар 2 ур. + 2 шара 3 ур.
    5: {3: 1, 4: 2},  # Шар 5 ур. = 1 шар 3 ур. + 2 шара 4 ур.
    6: {3: 1, 5: 2},  # Шар 6 ур. = 1 шар 3 ур. + 2 шара 5 ур.
    7: {4: 1, 5: 1, 6: 1},  # Шар 7 ур. = 1 шар 4 ур. + 1 шар 5 ур. + 1 шар 6 ур.
    8: {5: 1, 6: 1, 7: 1},  # Шар 8 ур. = 1 шар 5 ур. + 1 шар 6 ур. + 1 шар 7 ур.
    9: {6: 1, 7: 1, 8: 1},  # Шар 9 ур. = 1 шар 6 ур. + 1 шар 7 ур. + 1 шар 8 ур.
    10: {7: 1, 8: 1, 9: 1},  # Шар 10 ур. = 1 шар 7 ур. + 1 шар 8 ур. + 1 шар 9 ур.
    11: {8: 1, 9: 1, 10: 1},  # Шар 11 ур. = 1 шар 8 ур. + 1 шар 9 ур. + 1 шар 10 ур.
    12: {9: 1, 10: 1, 11: 1},  # Шар 12 ур. = 1 шар 9 ур. + 1 шар 10 ур. + 1 шар 11 ур.
}

# Шансы дропа из золотого яйца (только для шаров 1-3 уровня)
EGG_DROPS = [1, 2, 3, 0]  # 0 = Камень бессмертных (в расчетах не используется)
EGG_WEIGHTS = [0.71, 0.11, 0.08, 0.10]  # Вероятности выпадения: 71%, 11%, 8%, 10%

# Эквивалент дропа яйца в "шарах 1 ур" для расчета примерного количества яиц
EGG_EQUIV = 0.71 * 1 + 0.11 * 4 + 0.08 * 10  # ≈ 1.95


def load_icons(path="icons", size=(26, 26)):
    """
    Загружает иконки шаров из папки.

    Args:
        path (str): Путь к папке с иконками
        size (tuple): Размер иконок (ширина, высота)

    Returns:
        dict: Словарь с загруженными иконками {уровень: PhotoImage}
    """
    icons = {}

    # Загружаем иконки для шаров 1-12 уровней
    for i in range(1, 13):
        file = os.path.join(path, f"{i}.png")  # Формируем путь к файлу
        if os.path.exists(file):  # Проверяем существование файла
            img = Image.open(file).resize(size, Image.LANCZOS)  # Открываем и изменяем размер
            icons[i] = ImageTk.PhotoImage(img)  # Сохраняем как PhotoImage

    # Загружаем иконку золотого яйца
    egg_file = os.path.join(path, "goldegg.png")
    if os.path.exists(egg_file):
        img = Image.open(egg_file).resize(size, Image.LANCZOS)
        icons["egg"] = ImageTk.PhotoImage(img)

    return icons


def build_plan(orig_inventory, target_level, target_count=1):
    """
    Строит план крафта целевых шаров из имеющихся материалов.

    Args:
        orig_inventory (dict): Исходный инвентарь {уровень: количество}
        target_level (int): Уровень целевого шара (1-12)
        target_count (int): Количество целевых шаров

    Returns:
        tuple: (нехватка шаров 1 ур., словарь крафтов, остатки инвентаря)
    """
    # Создаем глубокую копию инвентаря для работы
    inv = defaultdict(int, copy.deepcopy(orig_inventory))
    # Словарь для подсчета сколько каких шаров нужно скрафтить
    make_counts = defaultdict(int)
    # Счетчик недостающих шаров 1-го уровня
    need_first = 0

    def produce(level, count):
        """
        Рекурсивная функция для производства шаров нужного уровня.

        Args:
            level (int): Уровень шара для производства
            count (int): Количество шаров для производства
        """
        nonlocal need_first  # Используем переменную из внешней функции

        if count <= 0:  # Если производить нечего - выходим
            return

        if level == 1:  # Дошли до шаров 1-го уровня
            if inv[1] >= count:  # Если шаров хватает
                inv[1] -= count  # Берем из инвентаря
            else:  # Если шаров не хватает
                need_first += (count - inv[1])  # Запоминаем недостачу
                inv[1] = 0  # Обнуляем остаток
            return

        # Если нужные шары уже есть в инвентаре
        if inv[level] >= count:
            inv[level] -= count  # Берем из инвентаря
            return

        # Вычисляем сколько шаров нужно создать
        need = count - inv[level]
        inv[level] = 0  # Обнуляем остаток этого уровня

        # Рекурсивно производим компоненты для крафта
        for sub_level, qty_per_unit in recipes[level].items():
            produce(sub_level, qty_per_unit * need)

        # Запоминаем сколько шаров этого уровня нужно создать
        make_counts[level] += need

    # Запускаем процесс производства целевых шаров
    produce(target_level, target_count)

    return need_first, make_counts, inv


def simulate_eggs(num_eggs):
    """
    Симулирует открытие золотых яиц и возвращает выпавшие шары.

    Args:
        num_eggs (int): Количество открываемых яиц

    Returns:
        dict: Словарь с выпавшими шарами {уровень: количество}
    """
    counts = defaultdict(int)  # Словарь для подсчета выпадений

    # Открываем каждое яйцо
    for _ in range(num_eggs):
        # Выбираем выпавший предмет согласно вероятностям
        drop = random.choices(EGG_DROPS, weights=EGG_WEIGHTS)[0]
        if drop in [1, 2, 3]:  # Если выпал шар (а не камень)
            counts[drop] += 1  # Увеличиваем счетчик

    return counts


def insert_with_icon(text_widget, text, lvl=None, end="\n", font_style=None):
    """
    Вставляет текст и иконку в текстовое поле.

    Args:
        text_widget: Виджет текстового поля
        text (str): Текст для вставки
        lvl (int/str): Уровень шара для иконки или "egg" для яйца
        end (str): Символ(ы) для вставки после текста/иконки
        font_style: Стиль шрифта для текста
    """
    if font_style:
        text_widget.insert(tk.END, text, font_style)  # Вставляем текст с указанным стилем
    else:
        text_widget.insert(tk.END, text)  # Вставляем текст

    if lvl in icons:  # Если есть иконка для этого уровня/яйца
        text_widget.image_create(tk.END, image=icons[lvl])  # Вставляем иконку

    if end:  # Если нужно добавить завершающие символы
        if font_style:
            text_widget.insert(tk.END, end, font_style)  # Вставляем их с указанным стилем
        else:
            text_widget.insert(tk.END, end)  # Вставляем их


def update_target_icon(event=None):
    """
    Обновляет иконку цели при изменении значения в поле ввода.
    """
    try:
        target_level = int(target_entry.get() or "0")
        if 1 <= target_level <= 12 and target_level in icons:
            target_icon_label.config(image=icons[target_level])
        else:
            # Если уровень некорректен, показываем пустую метку
            target_icon_label.config(image='')
    except ValueError:
        # Если введено не число, показываем пустую метку
        target_icon_label.config(image='')


def create_tooltip(widget, text):
    """
    Создает всплывающую подсказку для виджета.
    """
    tooltip = tk.Toplevel(widget)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry("+0+0")
    tooltip.withdraw()

    label = tk.Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1,
                     font=("Arial", 8), wraplength=200)
    label.pack()

    def show_tooltip(event):
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        tooltip.wm_geometry(f"+{x}+{y}")
        tooltip.deiconify()

    def hide_tooltip(event):
        tooltip.withdraw()

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)
    widget.bind("<Motion>", show_tooltip)

    return tooltip


def get_recipe_text(level):
    """
    Возвращает текстовое описание рецепта для указанного уровня.
    """
    if level == 1:
        return "Шар 1* - базовый предмет\nВыпадает из золотых яиц"

    if level not in recipes:
        return f"Рецепт для шара {level}* не найден"

    recipe = recipes[level]
    components = []
    for comp_level, quantity in recipe.items():
        components.append(f"{quantity} — {comp_level}*")

    return f"Шар {level}* крафтится из:\n" + "\n".join(components)


def on_calculate():
    """Обрабатывает нажатие кнопки 'Рассчитать'."""
    try:
        # Считываем инвентарь из полей ввода
        inventory = {}
        for i in range(1, 13):
            val_str = entries[i].get().strip()
            val = int(val_str) if val_str else 0  # Пустое поле = 0
            if val < 0:  # Проверяем на отрицательные значения
                raise ValueError
            inventory[i] = val  # Сохраняем в словарь

        # Считываем количество золотых яиц
        egg_str = egg_entry.get().strip()
        eggs = int(egg_str) if egg_str else 0  # Пустое поле = 0
        if eggs < 0:  # Проверяем на отрицательные значения
            raise ValueError

        # Считываем целевой уровень и количество
        target_str = target_entry.get().strip()
        target = int(target_str) if target_str else 0  # Пустое поле = 0
        if not (1 <= target <= 12):  # Проверяем корректность уровня
            messagebox.showerror("Ошибка", "Целевой уровень должен быть от 1 до 12.")
            return

        qty_str = qty_entry.get().strip()
        qty = int(qty_str) if qty_str else 0  # Пустое поле = 0
        if qty <= 0:  # Проверяем корректность количества
            messagebox.showerror("Ошибка", "Количество целей должно быть положительным.")
            return

        # Очищаем поле результатов
        result_text.delete(1.0, tk.END)

        # Симуляция открытия золотых яиц (если указано)
        if eggs > 0:
            egg_counts = simulate_eggs(eggs)  # Симулируем открытие яиц

            # Формат вывода: "Результат открытия Х (иконка яйца)"
            result_text.insert(tk.END, "Результат открытия ", "bold")
            insert_with_icon(result_text, f"{eggs} ", "egg", "", "bold")
            result_text.insert(tk.END, " :  ", "bold")

            # Выводим результаты открытия яиц
            for lvl in range(1, 4):
                if egg_counts[lvl] > 0:
                    insert_with_icon(result_text, f"{egg_counts[lvl]} ", lvl, "", "bold")
                    result_text.insert(tk.END, f"({lvl}*)   ", "bold")
                    inventory[lvl] += egg_counts[lvl]  # Добавляем в инвентарь

            result_text.insert(tk.END, "\n\n")

        # Рассчитываем план крафта
        need_first, make_counts, inv = build_plan(inventory, target, qty)

        # Если не хватает шаров 1-го уровня
        if need_first > 0:
            result_text.insert(tk.END, "Не хватает шаров для полного крафта.\n", "bold_red")
            insert_with_icon(result_text, f"Докупить {need_first} ", 1, "", "bold_red")
            result_text.insert(tk.END, " (1*)\n", "bold_red")

            # Рассчитываем примерное количество яиц для докупки
            approx_eggs = int(round(need_first / EGG_EQUIV))
            result_text.insert(tk.END, "Или примерно докупить ", "bold_red")
            insert_with_icon(result_text, f"{approx_eggs} ", "egg", "", "bold_red")
            return

        # Выводим пошаговый план крафта
        step = 1
        for lvl in range(2, target + 1):  # Для каждого уровня от 2 до целевого
            count_to_make = make_counts.get(lvl, 0)  # Сколько нужно создать
            if count_to_make <= 0:  # Если создавать не нужно - пропускаем
                continue

            # Формируем список компонентов для крафта
            parts = []
            for sub, qty_per_unit in recipes[lvl].items():
                used = qty_per_unit * count_to_make  # Общее количество компонентов
                parts.append((used, sub))  # Сохраняем (количество, уровень)

            # Выводим шаг крафта
            result_text.insert(tk.END, f"{step}. Крафти ", "bold")
            insert_with_icon(result_text, f"{count_to_make} ", lvl, " ", "bold_red")
            result_text.insert(tk.END, f"({lvl}*) из: ", "bold")

            # Выводим компоненты для крафта
            for idx, (used, sub) in enumerate(parts):
                insert_with_icon(result_text, f"{used} ", sub, "", "bold")
                if idx < len(parts) - 1:  # Если не последний компонент
                    result_text.insert(tk.END, " + ", "bold")  # Добавляем разделитель

            result_text.insert(tk.END, "\n")
            step += 1

        # Выводим итоговый результат
        result_text.insert(tk.END, f"\nГотово: {qty} × ", "bold_large")
        insert_with_icon(result_text, f"({target}*)", target, "\n", "bold_large")

        # Выводим остатки инвентаря после крафта
        result_text.insert(tk.END, "\nОстатки после крафта:  ", "bold")
        has_remains = False
        for lvl in range(1, 13):
            if inv[lvl] > 0:  # Если есть остатки этого уровня
                has_remains = True
                insert_with_icon(result_text, f"{inv[lvl]} ", lvl, "", "bold")
                result_text.insert(tk.END, f"({lvl}*)  ", "bold")
        if not has_remains:
            result_text.insert(tk.END, "ты без лишних денег(((", "bold")

    except ValueError:  # Обработка ошибок ввода
        messagebox.showerror("Ошибка", "Пожалуйста, вводите целые неотрицательные числа.")


# Создаем главное окно
root = tk.Tk()
root.title("Калькулятор шаров Perfect World | by Sogerero")

# Устанавливаем размер окна 800x980 пикселей
root.geometry("800x980")

# Настраиваем стили шрифтов
bold_font = ("Segoe UI", 10, "bold")
bold_large_font = ("Segoe UI", 12, "bold")
bold_red_font = ("Comic Sans MS", 11, "bold")

# Загружаем иконки
icons = load_icons("icons")
if 12 in icons:  # Устанавливаем иконку окна (шар 12 ур.)
    root.iconphoto(False, icons[12])

# Создаем основной фрейм с двумя колонками
main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=8)

# Левая колонка - Имеющиеся предметы
left_frame = tk.Frame(main_frame)
left_frame.grid(row=0, column=0, padx=(0, 15), pady=5, sticky="n")

# Вертикальная черная линия разделения
separator = tk.Frame(main_frame, width=2, bg="black", height=400)
separator.grid(row=0, column=1, padx=5, pady=5, sticky="ns")

# Правая колонка - Что крафтим
right_frame = tk.Frame(main_frame)
right_frame.grid(row=0, column=2, padx=(15, 0), pady=5, sticky="n")

# Создаем словарь для хранения полей ввода
entries = {}

# Настраиваем теги для текстового поля
result_text = scrolledtext.ScrolledText(root, width=80, height=40, wrap=tk.WORD, font=("Arial", 10))
result_text.tag_configure("bold", font=bold_font)
result_text.tag_configure("bold_large", font=bold_large_font)
result_text.tag_configure("bold_red", font=bold_red_font, foreground="red")

# Заголовок для левой колонки
tk.Label(left_frame, text="Имеющиеся предметы", font=bold_large_font).grid(row=0, column=0, columnspan=3, pady=(0, 10))

# Создаем поля ввода для каждого уровня шаров в левой колонке
icon_labels = {}  # Словарь для хранения меток с иконками
for i in range(1, 13):
    # Создаем текстовую метку с описанием (Уровень + иконка)
    tk.Label(left_frame, text=f"{i}*:", font=bold_font).grid(row=i, column=0, sticky="e", padx=(0, 5))

    # Создаем метку с иконкой
    if i in icons:
        icon_label = tk.Label(left_frame, image=icons[i])
        icon_label.grid(row=i, column=1, padx=2)
        icon_labels[i] = icon_label

        # Добавляем всплывающую подсказку с рецептом
        recipe_text = get_recipe_text(i)
        create_tooltip(icon_label, recipe_text)
    else:
        icon_label = tk.Label(left_frame, text="●", font=bold_font)
        icon_label.grid(row=i, column=1)
        icon_labels[i] = icon_label

    # Создаем поле ввода
    e = tk.Entry(left_frame, width=8, font=bold_font)
    e.grid(row=i, column=2, pady=1, padx=(5, 0))
    e.insert(0, "0")  # Устанавливаем значение по умолчанию
    entries[i] = e  # Сохраняем ссылку на поле ввода

# Создаем поле для ввода количества золотых яиц в левой колонке
row_egg = 13  # Следующая строка после полей для шаров

tk.Label(left_frame, text="Яйца:", font=bold_font).grid(row=row_egg, column=0, sticky="e", padx=(0, 5))

if "egg" in icons:  # Метка с иконкой яйца
    egg_icon_label = tk.Label(left_frame, image=icons["egg"])
    egg_icon_label.grid(row=row_egg, column=1, padx=2)
    # Добавляем подсказку для яйца
    egg_tooltip = "Золотое яйцо\nШансы выпадения:\n- Шар 1*: 71%\n- Шар 2*: 11%\n- Шар 3*: 8%\n- Камень бессмертных: 10%"
    create_tooltip(egg_icon_label, egg_tooltip)
else:
    tk.Label(left_frame, text="🥚", font=bold_font).grid(row=row_egg, column=1)

egg_entry = tk.Entry(left_frame, width=8, font=bold_font)
egg_entry.grid(row=row_egg, column=2, pady=1, padx=(5, 0))
egg_entry.insert(0, "0")  # Значение по умолчанию

# Заголовок для правой колонки
tk.Label(right_frame, text="Что крафтим?", font=bold_large_font).grid(row=0, column=0, columnspan=3, pady=(0, 10))

# Поле для ввода целевого уровня в правой колонке
row_target = 1

tk.Label(right_frame, text="Цель:", font=bold_font).grid(row=row_target, column=0, sticky="e", padx=(0, 5), pady=(6, 0))

# Метка для иконки цели
target_icon_label = tk.Label(right_frame)
target_icon_label.grid(row=row_target, column=1, padx=2)

# Добавляем подсказку для иконки цели
target_tooltip = create_tooltip(target_icon_label, "")


def update_target_tooltip(event=None):
    try:
        target_level = int(target_entry.get().strip() or "0")
        if 1 <= target_level <= 12:
            recipe_text = get_recipe_text(target_level)
            target_tooltip.children['!label'].config(text=recipe_text)
    except ValueError:
        pass


target_entry = tk.Entry(right_frame, width=8, font=bold_font)
target_entry.grid(row=row_target, column=2, pady=(6, 0), padx=(5, 0))
target_entry.insert(0, "12")  # Значение по умолчанию - максимальный уровень

# Привязываем обработчики для обновления иконки и подсказки
target_entry.bind('<KeyRelease>', update_target_icon)
target_entry.bind('<KeyRelease>', update_target_tooltip, add='+')

# Обновляем иконку цели и подсказку при запуске
update_target_icon()
update_target_tooltip()

# Поле для ввода количества целевых шаров в правой колонке
tk.Label(right_frame, text="Кол-во:", font=bold_font).grid(row=row_target + 1, column=0, sticky="e", padx=(0, 5),
                                                           pady=(10, 0))

# Пустая метка для выравнивания (вместо иконки)
tk.Label(right_frame, text="", width=2).grid(row=row_target + 1, column=1)

qty_entry = tk.Entry(right_frame, width=8, font=bold_font)
qty_entry.grid(row=row_target + 1, column=2, pady=(10, 0), padx=(5, 0))
qty_entry.insert(0, "1")  # Значение по умолчанию

# Стили для объемной кнопки
button_style = {
    "font": ("Century Gothic", 12, "bold"),
    "bg": "#4CAF50",  # Зеленый цвет
    "fg": "white",
    "activebackground": "#45a049",
    "activeforeground": "white",
    "relief": "raised",
    "bd": 4,
    "padx": 10,
    "pady": 5
}

# Кнопка для запуска расчета с объемным эффектом (располагаем под двумя колонками)
calc_button = tk.Button(main_frame, text="РАССЧИТАТЬ", command=on_calculate, **button_style)
calc_button.grid(row=1, column=0, columnspan=3, pady=(20, 8))

# Упаковываем текстовое поле с прокруткой для вывода результатов
result_text.pack(padx=10, pady=(0, 10), fill="both", expand=True)

# Запускаем главный цикл обработки событий
root.mainloop()