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

    def add_balance(self, amount):
        self.balance += amount


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

    def remove_item(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

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

        # Подключение обработчиков
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка обработчиков команд."""
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            chat_id = message.chat.id
            self.bot.send_message(chat_id, 'Добро пожаловать в наше кафе "Delicious_Moment"!')
            self.bot.send_message(chat_id, 'Пожалуйста, зарегистрируйтесь. Введите ваше имя:')
            self.bot.register_next_step_handler(message, self.register_user)

        @self.bot.message_handler(content_types=['text'])
        def handle_text(message):
            chat_id = message.chat.id
            if message.text == 'Меню':
                self.show_menu(message)
            elif message.text.isdigit():
                self.add_to_cart(message)
            elif message.text == 'Посмотреть корзину':
                self.show_cart(message)
            elif message.text == 'Ваши данные':
                self.show_user_data(message)
            elif message.text == 'Посмотреть баланс':
                self.show_balance(message)
            else:
                self.bot.send_message(chat_id, 'Неизвестная команда.')

        @self.bot.callback_query_handler(func=lambda call: call.data == "payment")
        def handle_payment_callback(call):
            self.process_payment(call.message)

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
        self.bot.send_message(chat_id, 'Вы успешно зарегистрированы!')

    def show_menu(self, message):
        chat_id = message.chat.id
        menu_text = "МЕНЮ:\n" + "\n".join([f"{i+1}) {item} — {price} руб." for i, (item, price) in enumerate(self.menu.items.items())])
        self.bot.send_message(chat_id, menu_text)

    def add_to_cart(self, message):
        chat_id = message.chat.id
        cart = self.get_cart(chat_id)
        menu = self.menu.items
        dish_number = int(message.text) - 1

        if 0 <= dish_number < len(menu):
            item = list(menu.keys())[dish_number]
            cart.add_item(item)
            self.bot.send_message(chat_id, f'{item} добавлено в корзину.')

    def show_cart(self, message):
        chat_id = message.chat.id
        cart = self.get_cart(chat_id)
        if cart.items:
            cart_text = "Корзина:\n" + "\n".join([f"{i+1}) {item}" for i, item in enumerate(cart.items)])
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Оплата", callback_data="payment"))
            self.bot.send_message(chat_id, cart_text, reply_markup=markup)
        else:
            self.bot.send_message(chat_id, 'Корзина пуста.')

    def show_user_data(self, message):
        """Отображение данных пользователя."""
        chat_id = message.chat.id
        user = self.users.get(chat_id)
        if user:
            self.bot.send_message(
                chat_id,
                f"Ваши данные:\nИмя: {user.name}\nБонусный баланс: {user.balance:.2f} руб."
            )
        else:
            self.bot.send_message(chat_id, "Вы не зарегистрированы. Используйте команду /start для регистрации.")

    def show_balance(self, message):
        """Отображение баланса пользователя."""
        chat_id = message.chat.id
        user = self.users.get(chat_id)
        if user:
            self.bot.send_message(
                chat_id,
                f"Ваш бонусный баланс: {user.balance:.2f} руб."
            )
        else:
            self.bot.send_message(chat_id, "Вы не зарегистрированы. Используйте команду /start для регистрации.")

    def get_cart(self, chat_id):
        return self.carts.setdefault(chat_id, Cart())

    def process_payment(self, message):
        chat_id = message.chat.id
        cart = self.get_cart(chat_id)
        total = cart.get_total(self.menu.items)
        user = self.users.setdefault(chat_id, User(chat_id))
        
        # Добавляем бонусы пользователю
        bonus = total * 0.1
        user.add_balance(bonus)
        
        # Очищаем корзину
        cart.clear()
        
        # Сообщаем о результате оплаты
        self.bot.send_message(
            chat_id,
            f'Оплата прошла успешно! Сумма: {total} руб. Вы получили {bonus:.2f} бонусов. Ваш общий баланс бонусов: {user.balance:.2f} руб.'
        )

    def run(self):
        self.bot.polling(none_stop=True)


# Запуск
if __name__ == '__main__':
    TOKEN = '7588996191:AAHsD186wzDG_ALZzjcDRWWA0KmcX3rFCQo'
    app = BotApp(TOKEN)
    app.run()
