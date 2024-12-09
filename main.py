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
    def __init__(self, chat_id, name=None, balance=0):
        self.chat_id = chat_id
        self.name = name
        self.balance = balance
        self.bonus_points = 0  
    def add_balance(self, amount):
        self.balance += amount

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
    """Класс для управления корзиной."""
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)

    def get_total(self, menu):
        return sum(menu[item] for item in self.items if item in menu)

    def clear(self):
        self.items.clear()


class BotApp:
    """Основной класс приложения."""
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.database = DatabaseManager()
        self.menu = Menu()
        self.users = {}
        self.carts = {}
        self.waiting_for_removal = {}  

        
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

    def register_user(self, message):
        chat_id = message.chat.id
        name = message.text.strip()
        self.bot.send_message(chat_id, 'Введите пароль:')
        self.bot.register_next_step_handler(message, self.save_user, name)

    def save_user(self, message, name):
        chat_id = message.chat.id
        password = message.text.strip()
        self.database.add_user(chat_id, name, password)
        self.users[chat_id] = User(chat_id, name)
        self.carts[chat_id] = Cart()

        # Создаем клавиатуру с кнопками
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Меню', 'Посмотреть корзину')
        markup.add('Ваши данные', 'Посмотреть баланс')
        markup.add('Удалить из корзины', 'Оплата')  
       
        self.bot.send_message(chat_id, 'Вы успешно зарегистрированы!', reply_markup=markup)

    def show_menu(self, message):
        chat_id = message.chat.id
        menu_text = "МЕНЮ:\n" + "\n".join([f"{i+1}) {item} — {price} руб." for i, (item, price) in enumerate(self.menu.items.items())])
        self.bot.send_message(chat_id, menu_text)
        self.bot.send_message(chat_id, "Введите номер блюда, чтобы добавить его в корзину.")

    def show_cart(self, message):
        chat_id = message.chat.id
        cart = self.get_cart(chat_id)
        if cart.items:
            cart_text = "Корзина:\n" + "\n".join([f"{i+1}) {item}" for i, item in enumerate(cart.items)])
            self.bot.send_message(chat_id, cart_text)
        else:
            self.bot.send_message(chat_id, 'Корзина пуста.')

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
            self.bot.send_message(chat_id, f"Ваши данные:\nИмя: {user.name}\nБонусный баланс: {user.bonus_points:.2f} руб.")
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
