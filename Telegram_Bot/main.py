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
def help_main(message):
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
def request_city(message):
    user = User.get_user(message.from_user.id)
    user.command = message.text
    if message.text == "/lowprice" or message.text == "/highprice" or message.text == '/bestdeal':
        bot.send_message(message.chat.id, "Введите город для поиска:")
        bot.register_next_step_handler(message, get_city)


def get_city(message):

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

def request_hotels_count(message, res):
    user = User.get_user(message.from_user.id)

    for index in range(len(res)):
        if res[index][1] == message.text:
            user.city_id = int(res[index][0])
            break
        else:
            bot.send_message(message.chat.id, 'Такого города нет в списке!')
            help_main(message)

    if user.city_id:
        bot.send_message(message.chat.id, "Сейчас Вы должны выбрать дату приезда в отель")
        user.date_1 = None
        user.date_2 = None
        start_calendar(message)

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
        bot.edit_message_text("Теперь выберите дату выезда из отеля.", call.message.chat.id,
                              call.message.message_id)
        call.message.text = res
        get_date(call.message)

def get_date(message):
    user = User.get_user(message.chat.id)
    if user.date_1 is None:
        user.date_1 = message.text
        start_calendar(message)
    else:
        user.date_2 = message.text
        date_1 = user.date_1
        date_2 = user.date_2
        result = lowprice.search_hotels(user.city_id, date_1, date_2)
        bot.send_message(message.chat.id, "Нужны ли Вам фотографии отеля?")
        bot.register_next_step_handler(message, show_photo, result)

def show_photo(message, res):
    if message == "Нет" or "нет" or "No" or "no":
        bot.send_message(message.chat.id, f"Сколько отелей Вам показать? Максимально {len(res)}")
        bot.register_next_step_handler(message, show_hotels, res)
    elif message == "Да" or "да" or "Yes" or "yes":
        pass

def show_hotels(message, result):
    for count in range(int(message.text)):
        for hotel in result:
            bot.send_message(message.chat.id, "Ccылка на отель: hotels.com/ho{link}\nНазвание отеля: {name_hotel}\n",
                                              "Адрес: {address}\nРейтинг отеля: {ratings}\nГород: {city}\n",
                                              "Цена: {price}").format(link=hotel[0],
                                                                      name_hotel=hotel[1],
                                                                      address=hotel[2],
                                                                      ratings=hotel[3],
                                                                      city=hotel[4],
                                                                      price=hotel[5])


if __name__ == "__main__":
    bot.polling(non_stop=True)
