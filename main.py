import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk  # Для работы с изображениями

def initialize_database():
    conn = sqlite3.connect("travel_agency.db")
    cursor = conn.cursor()

    # Таблица туров
    cursor.execute('''CREATE TABLE IF NOT EXISTS tours (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        image TEXT,
                        price REAL NOT NULL,
                        tickets INTEGER NOT NULL,
                        status TEXT NOT NULL CHECK(status IN ('актуален', 'не актуален')),
                        type TEXT NOT NULL
                      )''')

    # Таблица отелей
    cursor.execute('''CREATE TABLE IF NOT EXISTS hotels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        stars INTEGER NOT NULL CHECK(stars BETWEEN 0 AND 5),
                        country TEXT NOT NULL,
                        description TEXT NOT NULL,
                        tours_count INTEGER DEFAULT 0
                      )''')

    # Таблица стран
    cursor.execute('''CREATE TABLE IF NOT EXISTS countries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                      )''')

    # Добавляем примерные данные для стран
    cursor.execute("INSERT OR IGNORE INTO countries (name) VALUES ('Россия'), ('Франция'), ('Италия')")

    conn.commit()
    conn.close()

def load_hotels(tree, items_per_page, current_page, total_pages, pagination_label):
    """Загружает отели для текущей страницы."""
    conn = sqlite3.connect("travel_agency.db")
    cursor = conn.cursor()

    # Подсчет общего числа записей
    cursor.execute("SELECT COUNT(*) FROM hotels")
    total_records = cursor.fetchone()[0]
    total_pages.set((total_records + items_per_page - 1) // items_per_page)

    # Вычисляем LIMIT и OFFSET
    offset = (current_page.get() - 1) * items_per_page
    cursor.execute("SELECT id, name, stars, country, tours_count FROM hotels LIMIT ? OFFSET ?", 
                   (items_per_page, offset))
    rows = cursor.fetchall()
    conn.close()

    # Очистка таблицы
    for row in tree.get_children():
        tree.delete(row)

    # Заполнение таблицы
    for row in rows:
        tree.insert("", "end", values=row)

    # Обновляем информацию о страницах
    pagination_label.config(text=f"Страница {current_page.get()} из {total_pages.get()}")


def open_add_edit_hotel_window(tree, items_per_page, current_page, total_pages, pagination_label, edit=False):
    """Открывает окно для добавления или редактирования отеля."""
    window_title = "Редактировать отель" if edit else "Добавить отель"
    add_edit_window = tk.Toplevel()
    add_edit_window.title(window_title)
    add_edit_window.geometry("400x400")

    # Поля ввода
    tk.Label(add_edit_window, text="Название отеля:").pack(pady=5)
    name_entry = tk.Entry(add_edit_window)
    name_entry.pack(pady=5)

    tk.Label(add_edit_window, text="Количество звезд (0-5):").pack(pady=5)
    stars_entry = tk.Entry(add_edit_window)
    stars_entry.pack(pady=5)

    tk.Label(add_edit_window, text="Страна:").pack(pady=5)
    country_entry = tk.Entry(add_edit_window)
    country_entry.pack(pady=5)

    tk.Label(add_edit_window, text="Описание:").pack(pady=5)
    description_text = tk.Text(add_edit_window, height=5, width=40)
    description_text.pack(pady=5)

    if edit:
        # Получаем выбранный отель
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите отель для редактирования!")
            add_edit_window.destroy()
            return

        # Заполняем поля данными
        item = tree.item(selected_item)
        hotel_id, name, stars, country, tours_count = item['values']
        name_entry.insert(0, name)
        stars_entry.insert(0, stars)
        country_entry.insert(0, country)
        description_text.insert("1.0", tours_count)

    def save_hotel():
        name = name_entry.get().strip()
        stars = stars_entry.get().strip()
        country = country_entry.get().strip()
        description = description_text.get("1.0", tk.END).strip()

        # Проверка заполнения полей
        if not (name and stars.isdigit() and country and description):
            messagebox.showerror("Ошибка", "Заполните все поля корректно!")
            return

        stars = int(stars)
        if stars < 0 or stars > 5:
            messagebox.showerror("Ошибка", "Количество звезд должно быть от 0 до 5!")
            return

        conn = sqlite3.connect("travel_agency.db")
        cursor = conn.cursor()

        if edit:
            # Обновление отеля
            cursor.execute('''UPDATE hotels SET name = ?, stars = ?, country = ?, description = ? WHERE id = ?''',
                           (name, stars, country, description, hotel_id))
        else:
            # Добавление нового отеля
            cursor.execute('''INSERT INTO hotels (name, stars, country, description) VALUES (?, ?, ?, ?)''',
                           (name, stars, country, description))

        conn.commit()
        conn.close()
        load_hotels(tree, items_per_page, current_page, total_pages, pagination_label)
        add_edit_window.destroy()

    tk.Button(add_edit_window, text="Сохранить", command=save_hotel).pack(pady=10)


def delete_hotel(tree, items_per_page, current_page, total_pages, pagination_label):
    """Удаляет выбранный отель."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Ошибка", "Выберите отель для удаления!")
        return

    # Получаем ID отеля
    item = tree.item(selected_item)
    hotel_id, name, stars, country, tours_count = item['values']

    # Проверка связи с турами
    if tours_count > 0:
        messagebox.showerror("Ошибка", f"Отель \"{name}\" связан с турами и не может быть удален!")
        return

    # Подтверждение удаления
    if not messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить отель \"{name}\"?"):
        return

    conn = sqlite3.connect("travel_agency.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hotels WHERE id = ?", (hotel_id,))
    conn.commit()
    conn.close()

    load_hotels(tree, items_per_page, current_page, total_pages, pagination_label)
    messagebox.showinfo("Успех", f"Отель \"{name}\" успешно удален!")



def add_sample_hotels():
    """Добавляет тестовые данные в таблицу отелей."""
    conn = sqlite3.connect("travel_agency.db")
    cursor = conn.cursor()

    # Проверяем, есть ли данные
    cursor.execute("SELECT COUNT(*) FROM hotels")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''INSERT INTO hotels (name, stars, country, description, tours_count) 
                              VALUES (?, ?, ?, ?, ?)''', [
            ("Отель Москва", 5, "Россия", "Роскошный отель в центре Москвы", 3),
            ("Лазурный берег", 4, "Франция", "Отель с видом на море", 2),
            ("Горный курорт", 3, "Италия", "Уютный отель в Альпах", 1)
        ])
    conn.commit()
    conn.close()


def open_hotels_window():
    hotels_window = tk.Toplevel()
    hotels_window.title("Список отелей")
    hotels_window.geometry("800x600")

    # Заголовок
    tk.Label(hotels_window, text="Список отелей", font=("Arial", 16)).pack(pady=10)

    # Фрейм для управления страницами
    pagination_frame = tk.Frame(hotels_window)
    pagination_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

    # Фрейм для таблицы
    table_frame = tk.Frame(hotels_window)
    table_frame.pack(fill=tk.BOTH, expand=True)

    # Таблица отелей
    columns = ("id", "name", "stars", "country", "tours_count")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    tree.heading("id", text="ID")
    tree.heading("name", text="Название")
    tree.heading("stars", text="Звезды")
    tree.heading("country", text="Страна")
    tree.heading("tours_count", text="Кол-во туров")
    tree.pack(fill=tk.BOTH, expand=True)

        # Кнопки управления
    buttons_frame = tk.Frame(hotels_window)
    buttons_frame.pack(pady=10)

    tk.Button(buttons_frame, text="Добавить отель", command=lambda: open_add_edit_hotel_window(tree, items_per_page, current_page, total_pages, pagination_label)).pack(side=tk.LEFT, padx=5)
    tk.Button(buttons_frame, text="Редактировать отель", command=lambda: open_add_edit_hotel_window(tree, items_per_page, current_page, total_pages, pagination_label, edit=True)).pack(side=tk.LEFT, padx=5)
    tk.Button(buttons_frame, text="Удалить отель", command=lambda: delete_hotel(tree, items_per_page, current_page, total_pages, pagination_label)).pack(side=tk.LEFT, padx=5)


    # Параметры пагинации
    items_per_page = 10
    current_page = tk.IntVar(value=1)
    total_pages = tk.IntVar(value=1)

    def change_page(delta):
        """Меняет текущую страницу."""
        new_page = current_page.get() + delta
        if 1 <= new_page <= total_pages.get():
            current_page.set(new_page)
            load_hotels()

    # Кнопки управления страницами
    tk.Button(pagination_frame, text="<<", command=lambda: change_page(-1)).pack(side=tk.LEFT, padx=5)
    pagination_label = tk.Label(pagination_frame, text=f"Страница {current_page.get()} из {total_pages.get()}")
    pagination_label.pack(side=tk.LEFT, padx=5)
    tk.Button(pagination_frame, text=">>", command=lambda: change_page(1)).pack(side=tk.LEFT, padx=5)

    # Загрузка первой страницы
    load_hotels(tree, items_per_page, current_page, total_pages, pagination_label)



def add_sample_tours():
    conn = sqlite3.connect("travel_agency.db")
    cursor = conn.cursor()

    # Проверяем, есть ли данные
    cursor.execute("SELECT COUNT(*) FROM tours")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''INSERT INTO tours (name, image, price, tickets, status, type) 
                              VALUES (?, ?, ?, ?, ?, ?)''', [
            ("Золотое кольцо России", None, 15000, 20, "актуален", "Исторический"),
            ("Французская Ривьера", None, 85000, 5, "актуален", "Пляжный"),
            ("Альпы и Лазурный берег", None, 120000, 2, "не актуален", "Горнолыжный")
        ])
    conn.commit()
    conn.close()


def main_window():
    root = tk.Tk()
    root.title("Туристическое агентство")
    root.geometry("800x600")

    # Заголовок
    tk.Label(root, text="Список туров", font=("Arial", 16)).pack(pady=10)

    # Фрейм для фильтров
    filter_frame = tk.Frame(root)
    filter_frame.pack(pady=5)

        # Элементы управления сортировкой
    sort_frame = tk.Frame(root)
    sort_frame.pack(pady=5)

    tk.Label(sort_frame, text="Сортировать по цене:").pack(side=tk.LEFT, padx=5)
    sort_order_var = tk.StringVar(value="По умолчанию")
    sort_menu = ttk.Combobox(sort_frame, textvariable=sort_order_var, state="readonly")
    sort_menu['values'] = ["По умолчанию", "По возрастанию", "По убыванию"]
    sort_menu.pack(side=tk.LEFT, padx=5)


    # Поле поиска
    tk.Label(filter_frame, text="Поиск:").grid(row=0, column=0, padx=5)
    search_entry = tk.Entry(filter_frame, width=20)
    search_entry.grid(row=0, column=1, padx=5)

    # Фильтрация по типу
    tk.Label(filter_frame, text="Тип тура:").grid(row=0, column=2, padx=5)
    tour_type_var = tk.StringVar(value="Все типы")
    tour_type_menu = ttk.Combobox(filter_frame, textvariable=tour_type_var, state="readonly")
    tour_type_menu.grid(row=0, column=3, padx=5)

    # Чекбокс для фильтрации по актуальности
    show_actual_var = tk.BooleanVar(value=True)
    tk.Checkbutton(filter_frame, text="Только актуальные", variable=show_actual_var).grid(row=0, column=4, padx=5)

    # Фрейм для туров
    tours_frame = tk.Frame(root)
    tours_frame.pack(fill=tk.BOTH, expand=True)

    def load_tour_types():
        """Загружаем все типы туров в выпадающий список."""
        conn = sqlite3.connect("travel_agency.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT type FROM tours")
        types = [row[0] for row in cursor.fetchall()]
        conn.close()
        tour_type_menu['values'] = ["Все типы"] + types

    def load_tours():
        """Загружает туры с учетом поиска, фильтрации и сортировки."""
        conn = sqlite3.connect("travel_agency.db")
        cursor = conn.cursor()

        query = "SELECT name, image, price, tickets, status FROM tours WHERE 1=1"
        params = []

        # Фильтрация по поиску
        search_text = search_entry.get().strip()
        if search_text:
            query += " AND (name LIKE ? OR type LIKE ?)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])

        # Фильтрация по типу
        selected_type = tour_type_var.get()
        if selected_type and selected_type != "Все типы":
            query += " AND type = ?"
            params.append(selected_type)

        # Фильтрация по актуальности
        if show_actual_var.get():
            query += " AND status = ?"
            params.append("актуален")

        # Сортировка
        sort_order = sort_order_var.get()
        if sort_order == "По возрастанию":
            query += " ORDER BY price ASC"
        elif sort_order == "По убыванию":
            query += " ORDER BY price DESC"

        cursor.execute(query, params)
        tours = cursor.fetchall()
        conn.close()

        # Очистка старых виджетов
        for widget in tours_frame.winfo_children():
            widget.destroy()

        # Создание плиток
        for tour in tours:
            name, image_path, price, tickets, status = tour

            frame = tk.Frame(tours_frame, borderwidth=1, relief="solid", padx=10, pady=10)
            frame.pack(fill=tk.X, padx=5, pady=5)

            tk.Label(frame, text=name, font=("Arial", 14)).pack(anchor="w")
            tk.Label(frame, text=f"Цена: {price} РУБ", font=("Arial", 12)).pack(anchor="w")
            tk.Label(frame, text=f"Билеты: {tickets}", font=("Arial", 12)).pack(anchor="w")

            # Цвет статуса
            color = "green" if status == "актуален" else "red"
            tk.Label(frame, text=f"Статус: {status}", font=("Arial", 12), fg=color).pack(anchor="w")

            # Добавляем изображение
            image_path = image_path if image_path else "picture.png"
            try:
                image = Image.open(image_path)
                image = image.resize((100, 100), Image.ANTIALIAS)
                photo = ImageTk.PhotoImage(image)
                tk.Label(frame, image=photo).pack(side=tk.LEFT, padx=5)
                frame.image = photo  # Сохраняем ссылку на изображение
            except Exception as e:
                tk.Label(frame, text="[Ошибка загрузки изображения]").pack(side=tk.LEFT, padx=5)


    # Загрузка типов туров и туров
    load_tour_types()
    load_tours()
    # Привязка событий для сортировки
    sort_menu.bind("<<ComboboxSelected>>", lambda event: load_tours())


    # Привязка событий
    search_entry.bind("<KeyRelease>", lambda event: load_tours())
    tour_type_menu.bind("<<ComboboxSelected>>", lambda event: load_tours())
    show_actual_var.trace("w", lambda *args: load_tours())
    # Кнопка для перехода к таблице отелей
    tk.Button(root, text="Список отелей", command=open_hotels_window).pack(pady=10)
    root.mainloop()


# Инициализация базы данных
initialize_database()

# Добавление тестовых данных в отели
add_sample_hotels()

# Добавление тестовых данных в туры
add_sample_tours()

# Запуск главного окна
main_window()
