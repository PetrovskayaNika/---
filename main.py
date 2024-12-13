import telebot
import sqlite3
from telebot import types


class DatabaseManager:
    """Управление базой данных."""
    def __init__(self, db_name="telegram_register.sql"):
        self.db_name = db_name
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute('DROP TABLE IF EXISTS users')
        cur.execute(''' 
            CREATE TABLE users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                pass TEXT NOT NULL
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()

    def add_user(self, chat_id, name, password):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute('INSERT INTO users (chat_id, name, pass) VALUES (?, ?, ?)', (chat_id, name, password))
        conn.commit()
        cur.close()
        conn.close()

    def get_user(self, chat_id):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute('SELECT name, pass FROM users WHERE chat_id = ?', (chat_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user


class User:
    """Класс для управления данными пользователя."""
    def __init__(self, chat_id, name=None, balance=0, password=None):
        self.chat_id = chat_id
        self.name = name
        self.balance = balance
        self.bonus_points = 0
        self.password = password 
    def add_bonus(self, amount):
        self.bonus_points += amount  


class Menu:
    """Класс для управления меню."""
    def __init__(self):
        self.items = {
            "Капрезе с песто": 450,
            "Тартар из лосося с авокадо": 600,
            "Брускетта с прошутто и инжиром": 400,
            "Том Ям с креветками": 550,
            "Крем-суп из тыквы с имбирем": 350,
            "Филе миньон с картофельным пюре": 1200,
            "Ризотто с морепродуктами": 800,
            "Курица по-тайски с кешью": 700,
            "Тирамису": 300,
            "Шоколадный фонтан с ванильным мороженым": 500
        }


class Cart:
    """Класс для представления корзины пользователя."""
    def __init__(self):
        self.items = []

    def add_item(self, item):
        """Добавить блюдо в корзину."""
        self.items.append(item)

    def remove_item(self, item):
        """Удалить блюдо из корзины."""
        if item in self.items:
            self.items.remove(item)

    def get_total(self, menu_items):
        """Рассчитать общую стоимость корзины."""
        total = 0
        for item in self.items:
            total += menu_items[item]
        return total

    def clear(self):
        """Очистить корзину."""
        self.items = []
class Menu:
    """Меню с блюдами."""
    def __init__(self):
        # Пример меню с изображениями и ценами.
        self.items = {
            "Капрезе с песто": 450,
            "Тартар из лосося с авокадо": 600,
            "Брускетта с прошутто и инжиром": 400,
            "Том Ям с креветками": 550,
            "Крем-суп из тыквы с имбирем": 350,
            "Филе миньон с картофельным пюре": 1200,
            "Ризотто с морепродуктами": 800,
            "Курица по-тайски с кешью": 700,
            "Тирамису": 300,
            "Шоколадный фонтан с ванильным мороженым": 500
        }
        # Пути к изображениям для каждого блюда
        self.image_paths = {
            "Капрезе с песто": "images/caprese.jpg",
            "Тартар из лосося с авокадо": "images/tartar.jpg",
            "Брускетта с прошутто и инжиром": "images/brusket.jpg",
            "Том Ям с креветками": "images/tomym.jpg",
            "Крем-суп из тыквы с имбирем": "images/coup.jpg",
            "Филе миньон с картофельным пюре": "images/meet.jpeg",
            "Ризотто с морепродуктами": "images/rizoto.jpeg",
            "Курица по-тайски с кешью": "images/chekan_chiness.jpg",
            "Тирамису": "images/tiramisy.jpg",
            "Шоколадный фонтан с ванильным мороженым": "images/cokolate.jpeg",
        }

class BotApp:
    """Основной класс приложения."""
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.database = DatabaseManager()
        self.menu = Menu()
        self.users = {}
        self.carts = {}
        self.waiting_for_removal = {}  
        self.current_selection = {}  # Добавляем атрибут для хранения текущих выборов пользователя
        
        self.setup_handlers()

        
       

    def setup_handlers(self):
        """Настройка обработчиков команд."""
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            chat_id = message.chat.id
            self.bot.send_message(chat_id, 'Добро пожаловать в наше кафе "Delicious_Moment"! Пройдите регистрацию.')
            self.bot.send_message(chat_id, 'Введите ваше имя:')
            self.bot.register_next_step_handler(message, self.register_user)
        

        @self.bot.message_handler(content_types=['text'])
        def handle_text(message):
            chat_id = message.chat.id
            if message.text == 'Меню':
                self.show_menu(message)
            elif message.text == 'Посмотреть корзину':
                self.show_cart(message)
            elif message.text == 'Удалить из корзины':
                self.remove_from_cart(message)
            elif message.text == 'Оплата':
                self.process_payment(message)
            elif message.text == 'Ваши данные':
                self.show_user_data(message)
            elif message.text == 'Посмотреть баланс':
                self.show_bonus_balance(message)  
            elif message.text.isdigit():
                self.process_number_input(message)  
            else:
                self.bot.send_message(chat_id, "Неизвестная команда. Пожалуйста, выберите доступный вариант.")
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            chat_id = call.message.chat.id
            data = call.data
            if call.data.startswith("add_"):
                dish_name = call.data[4:]
                cart = self.get_cart(chat_id)
                cart.add_item(dish_name)
                self.bot.send_message(chat_id, f'Блюдо "{dish_name}" добавлено в корзину.')
            

            elif call.data == "cancel":
                self.bot.send_message(chat_id, "Вы отменили выбор.")

            elif call.data.startswith("select_"):
                dish_idx = int(call.data[7:]) - 1
                dish_name = list(self.menu.items.keys())[dish_idx]
                self.current_selection[chat_id] = dish_name
                self.show_dish_details(chat_id, dish_name)

    def show_menu(self, message):
        chat_id = message.chat.id
        menu_text = "МЕНЮ:\n" + "\n".join([f"{i+1}) {item} — {price} руб." for i, (item, price) in enumerate(self.menu.items.items())])
        self.bot.send_message(chat_id, menu_text)
        self.bot.send_message(chat_id, "Введите номер блюда, чтобы добавить его в корзину.")

        # Ждем номер блюда
        self.bot.register_next_step_handler(message, self.handle_dish_selection)
    
    def show_dish_details(self, chat_id, dish_name):
    # Показываем картинку и кнопки для добавления в корзину или отмены
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Добавить в корзину", callback_data=f"add_{dish_name}"))
        markup.add(types.InlineKeyboardButton("Отмена", callback_data="cancel"))

        # Если есть изображение блюда, показываем его
        if dish_name in self.menu.image_paths:
            image_path = self.menu.image_paths[dish_name]
            try:
                with open(image_path, 'rb') as image_file:
                    self.bot.send_photo(chat_id, image_file, caption=f"Вы выбрали блюдо: {dish_name}", reply_markup=markup)
            except FileNotFoundError:
                # Обработка случая, если файл не найден
                self.bot.send_message(chat_id, f"Изображение для блюда \"{dish_name}\" не найдено. Однако, блюдо добавлено в корзину.", reply_markup=markup)
            except Exception as e:
                # Обработка других ошибок при чтении файла
                self.bot.send_message(chat_id, f"Произошла ошибка при попытке загрузить изображение для блюда \"{dish_name}\". Ошибка: {e}", reply_markup=markup)
        else:
            self.bot.send_message(chat_id, f"Вы выбрали блюдо: {dish_name}", reply_markup=markup)



    def register_user(self, message):
        chat_id = message.chat.id
        name = message.text.strip()
        self.bot.send_message(chat_id, 'Введите пароль:')
        self.bot.register_next_step_handler(message, self.save_user, name)

    def save_user(self, message, name):
        chat_id = message.chat.id
        password = message.text.strip()
        self.database.add_user(chat_id, name, password)
        self.users[chat_id] = User(chat_id, name,password=password)
        self.carts[chat_id] = Cart()

        # Создаем клавиатуру с кнопками
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Меню', 'Посмотреть корзину')
        markup.add('Ваши данные', 'Посмотреть баланс')
        markup.add('Удалить из корзины', 'Оплата')  
       
        self.bot.send_message(chat_id, 'Вы успешно зарегистрированы!', reply_markup=markup)
    def show_menu(self, message):
        """Показать меню."""
        chat_id = message.chat.id
        menu_text = "Меню:\n"
        for idx, (item, price) in enumerate(self.menu.items.items(), 1):
            menu_text += f"{idx}. {item} — {price} руб.\n"

        self.bot.send_message(chat_id, menu_text)
        self.bot.send_message(chat_id, "Выберите номер блюда для подробностей:")

        # Ждем номер блюда
        self.bot.register_next_step_handler(message, self.handle_dish_selection)

    def handle_callback(self, call):
        """Обработка кнопок."""
        chat_id = call.message.chat.id
        if call.data.startswith("add_"):
            dish_name = call.data[4:]
            cart = self.get_cart(chat_id)
            cart.add_item(dish_name)
            self.bot.send_message(chat_id, f'Блюдо "{dish_name}" добавлено в корзину.')
        elif call.data == "cancel":
            self.bot.send_message(chat_id, "Вы отменили выбор.")

    def handle_dish_selection(self, message):
        chat_id = message.chat.id
        try:
            dish_number = int(message.text)
            if 1 <= dish_number <= len(self.menu.items):
                dish_name = list(self.menu.items.keys())[dish_number - 1]
                self.show_dish_details(chat_id, dish_name)  # Показываем снова детали выбранного блюда
            else:
                self.bot.send_message(chat_id, "Неверный номер блюда. Пожалуйста, выберите правильный номер из меню.")
                self.show_menu(message)  # Показываем меню снова
        except ValueError:
            self.bot.send_message(chat_id, "Пожалуйста, введите номер блюда.")
            self.show_menu(message)  # Показываем меню снова


    
    def show_cart(self, message):
        chat_id = message.chat.id
        cart = self.get_cart(chat_id)
        if not cart.items:
            self.bot.send_message(chat_id, "Ваша корзина пуста.")
        else:
            cart_content = "\n".join([ 
                f"{idx+1}. {item} — {self.menu.items[item]} руб." 
                for idx, item in enumerate(cart.items)
            ])
            total = cart.get_total(self.menu.items)
            self.bot.send_message(
                chat_id,
                f"Ваш заказ:\n{cart_content}\n\nИтого: {total} руб."
            )


    def remove_from_cart(self, message):
        chat_id = message.chat.id
        cart = self.get_cart(chat_id)
        if cart.items:
            self.waiting_for_removal[chat_id] = True  
            cart_text = "Корзина:\n" + "\n".join([f"{i+1}) {item}" for i, item in enumerate(cart.items)])
            self.bot.send_message(chat_id, cart_text)
            self.bot.send_message(chat_id, 'Введите номер блюда, чтобы удалить его из корзины.')
        else:
            self.bot.send_message(chat_id, 'Корзина пуста. Удалять нечего.')

    def process_number_input(self, message):
        chat_id = message.chat.id
        cart = self.get_cart(chat_id)

        if self.waiting_for_removal.get(chat_id): 
            try:
                number = int(message.text.strip()) - 1
                if 0 <= number < len(cart.items):
                    dish_name = cart.items[number]
                    cart.remove_item(dish_name)
                    self.bot.send_message(chat_id, f'Блюдо "{dish_name}" удалено из корзины.')
                    self.waiting_for_removal[chat_id] = False  
                    self.show_cart(message)  
                else:
                    self.bot.send_message(chat_id, 'Неверный номер блюда. Пожалуйста, выберите правильный номер.')
            except ValueError:
                self.bot.send_message(chat_id, 'Введите корректный номер блюда.')
        else:
            
            try:
                number = int(message.text.strip()) - 1
                if 0 <= number < len(self.menu.items):
                    dish_name = list(self.menu.items.keys())[number]
                    cart.add_item(dish_name)
                    self.bot.send_message(chat_id, f'Блюдо "{dish_name}" добавлено в корзину.')
                else:
                    self.bot.send_message(chat_id, 'Неверный номер блюда. Пожалуйста, выберите правильный номер.')
            except ValueError:
                self.bot.send_message(chat_id, 'Введите корректный номер блюда.')

    def show_user_data(self, message):
        chat_id = message.chat.id
        user = self.users.get(chat_id)
        if user:
            self.bot.send_message(chat_id,  f"Ваши данные:\nИмя: {user.name}\nПароль: {user.password}\nБонусный баланс: {user.bonus_points:.2f} руб.")
        else:
            self.bot.send_message(chat_id, "Вы не зарегистрированы. Используйте команду /start для регистрации.")

    def show_bonus_balance(self, message):
        chat_id = message.chat.id
        user = self.users.get(chat_id)
        if user:
            self.bot.send_message(chat_id, f"Ваш бонусный баланс: {user.bonus_points:.2f} руб.")
        else:
            self.bot.send_message(chat_id, "Вы не зарегистрированы. Используйте команду /start для регистрации.")

    def process_payment(self, message):
        chat_id = message.chat.id
        cart = self.get_cart(chat_id)
        total = cart.get_total(self.menu.items)
        user = self.users.get(chat_id)

        if total > 0:
            # Начисляем бонусы
            if user:
                bonus = total * 0.1 
                user.add_bonus(bonus)
                self.bot.send_message(chat_id, f"Вам начислено {bonus:.2f} бонусных рублей! Общий бонусный баланс: {user.bonus_points:.2f} руб.")

            cart.clear()
            self.bot.send_message(chat_id, f"С вас {total} руб. Спасибо за заказ!")
        else:
            self.bot.send_message(chat_id, "Ваша корзина пуста. Пожалуйста, добавьте блюда в корзину перед оплатой.")

    def get_cart(self, chat_id):
        if chat_id not in self.carts:
            self.carts[chat_id] = Cart()
        return self.carts[chat_id]

    def run(self):
        self.bot.infinity_polling()


if __name__ == "__main__":
    TOKEN = "7588996191:AAHsD186wzDG_ALZzjcDRWWA0KmcX3rFCQo"
    app = BotApp(TOKEN)
    app.run()
