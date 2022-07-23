import telebot
import os
import emoji

from users import User
from telebot import types
from decouple import config
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from botrequests import lowprice

TOKEN = config("TOKEN")

uid = os.environ
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def start_main(message):
    """
    Функция start_main. Привевствие бота
    """
    bot.send_message(message.chat.id, "Привет {first_name} {last_name}!\nЯ твой бот помощник по выбору отеля. "
                                      "Для получения информации о доступных командах введите /help".format(
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    ))

@bot.message_handler(commands=["help"])
def help_main(message: str) -> None:
    """
    Функция help_main. Бот подсказывает команды
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    key_low = types.KeyboardButton("/lowprice")
    key_high = types.KeyboardButton("/highprice")
    key_best = types.KeyboardButton("/bestdeal")
    key_history = types.KeyboardButton("/history")
    keyboard.add(key_low, key_high, key_best, key_history)
    bot.send_message(message.chat.id, "Доступные команды:\n/lowprice - Поможет Вам с поиском дешёвых отелей"
                                      "\n/highprie - Найдёт более дорогие отели."
                                      "\n/bestdeal - Укажите нужные Вам параметры и бот найдёт отель по вашим "
                                      "предпочтениям"
                                      "\n/history - История поисков", reply_markup=keyboard)

@bot.message_handler(content_types='text')
def request_city(message: str) -> None:
    """
    Функция request_city. Бот просит название города для поиска отеля
    """
    user = User.get_user(message.from_user.id)
    user.command = message.text
    if message.text == "/lowprice" or message.text == "/highprice" or message.text == '/bestdeal':
        bot.send_message(message.chat.id, "Введите город для поиска:")
        bot.register_next_step_handler(message, get_city)
    else:
        bot.send_message(message.chat.id, "Я тебя не понимаю!")


def get_city(message: str) -> None:
    """
    Функция get_city. Ищет список похожих городов и предлагает выбрать одно из них.
    """
    bot.send_message(message.chat.id, "Ожидайте. Идёт поиск городов.....")
    result = lowprice.search_city(message.text)

    markup_city = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if len(result) > 0:
        for i in range(len(result)):
            markup_city.add(types.KeyboardButton(f'{result[i][1]}'))
        markup_city.add(types.KeyboardButton('Отмена'))
        message = bot.send_message(message.chat.id, "Выберите город!", reply_markup=markup_city)
        bot.register_next_step_handler(message, request_hotels_count, result)
    else:
        bot.send_message(message.chat.id, "Я ничего не нашел (((")

def request_hotels_count(message: str, res: list) -> None:
    """
    Функция request_hotels_count.
    """

    user = User.get_user(message.from_user.id)

    for index in range(len(res)):
        if message.text in res[index][1]:
            user.city_id = int(res[index][0])
            break

    if user.city_id:
        bot.send_message(message.chat.id, "Сейчас Вы должны выбрать дату приезда в отель")
        user.date_1 = None
        user.date_2 = None
        start_calendar(message)
    else:
        bot.send_message(message.chat.id, "Такого города нет в списке!")
        help_main(message)

def start_calendar(message: types.Message) -> None:
    """Запускаем Календарь."""
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(message.chat.id, f"Выберите: {LSTEP[step]}", reply_markup=calendar)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(call: types.CallbackQuery) -> None:
    """Выбираем дату в календаре."""
    res, key, step = DetailedTelegramCalendar().process(call.data)
    if not res and key:
        bot.edit_message_text(f"Выберите: {LSTEP[step]}", call.message.chat.id, call.message.message_id,
                              reply_markup=key)
    elif res:
        bot.edit_message_text(f"Вы выбрали {res}", call.message.chat.id,
                              call.message.message_id)
        call.message.text = res
        get_date(call.message)

def get_date(message):
    user = User.get_user(message.chat.id)
    if user.date_1 is None:
        user.date_1 = message.text
        bot.send_message(message.chat.id, "Теперь выберите дату выезда из отеля.")
        start_calendar(message)
    else:
        user.date_2 = message.text
        date_1 = user.date_1
        date_2 = user.date_2
        delta = int((date_2 - date_1).days)
        if delta <= 0:
            bot.send_message(message.chat.id, "Вы не можете перемещаться во времени...\nПопробуйте ещё раз!")
            user.date_1 = None
            user.date_2 = None
            start_calendar(message)

        else:
            bot.send_message(message.chat.id, "Сколько отелей показать? Максимум 10.")
            bot.register_next_step_handler(message, request_hotels)

def request_hotels(message):
    user = User.get_user(message.chat.id)
    user.count_hotel = int(message.text)
    result = lowprice.search_hotels(user.count_hotel, user.date_1, user.date_2, user.city_id)
    if len(result) == 0:
        bot.send_message(message.chat.id, "В этом городе нет отелей!\nПоиск завершён.")
        help_main()
    else:
        bot.send_message(message.chat.id, "Показать фотографии? Да/Нет")
        bot.register_next_step_handler(message, ask_photo, result)

def show_hotel(hotel: list) -> str:
        mes = ""
        for info, v in hotel.items():
            join_info = str(info) + " " + str(v) + "\n"
            mes += join_info
        return mes

def ask_photo(message, res: list) -> None:

    if message.text == "Нет" or message.text == "нет":
        for i in res:
            bot.send_message(message.chat.id, show_hotel(i))
    elif message.text == "Да" or message.text == "да":
        bot.send_message(message.chat.id, "Сколько фотографий показать? Максимум 10.")
        bot.register_next_step_handler(message, show, res)

def show(message, res: list):
    user = User.get_user(message.chat.id)
    list_id_photo = [id["Ссылка на отель:"][13:] for id in res]
    list_photo = []
    for id in list_id_photo:
        url_photo = lowprice.search_photo(message.text, id)
        list_photo.append(url_photo)

    index = 0
    if user.count_hotel > len(res):
        bot.send_message(message.chat.id, "Я нашёл больше отелей!")
    # Показывает только 1 фотографию! Исправить
    for i in res:
        bot.send_message(message.chat.id, show_hotel(i))
        bot.send_message(message.chat.id, list_photo[index])
        index += 1
    bot.send_message(message.chat.id, "Поиск завершён!")


if __name__ == "__main__":
    bot.polling(non_stop=True)
