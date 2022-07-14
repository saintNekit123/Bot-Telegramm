import json
import requests
from decouple import config
from datetime import datetime
from requests.exceptions import Timeout, ConnectionError

api_key = config('API_KEY')
url = "https://hotels4.p.rapidapi.com/locations/v2/search"
url_hotels = "https://hotels4.p.rapidapi.com/properties/list"
url_photo = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': api_key
}


def search_city(city):
    querystring = {"query": city, "locale": "ru_RU", "currency": "RUB"}
    try:
        response = requests.request("GET", url, headers=headers, params=querystring, timeout=15)
        data = json.loads(response.text)
        id_city = data['suggestions'][0]['entities']
        total_list = []
        for info in id_city:
            list_city = []
            for name in info:
                if name == 'destinationId':
                    list_city.append(info[name])
                elif name == 'name':
                    list_city.append(info[name])
            total_list.append(list_city)
        return total_list

    except (Timeout, ConnectionError, KeyError, IndexError) as err:
        with open('logging.log', 'a') as file:
            file.write(f'\n{datetime.now()}, {type(err)}, search_city')
        return 'Вышло время запроса, или произошел сбой. Пожалуйста попробуйте еще раз!'


def search_hotels(id_city, date_1, date_2):
    querystring = {"query": id_city, "locale": "ru_RU", "currency": "RUB", "checkIn": date_1, "checkOut": date_2}
    try:
        response = requests.request("GET", id_city, headers=headers, params=querystring, timeout=15)
        data = json.loads(response.text)
        with open("hotels.json", "w") as file:
            json.dump(file, data, )

        # Ссылка на отель
        # Название отеля
        # Рейтинг
        # Город
        # Адрес
        # Центр города
        # Цена за вермя проживания
        # Цена за сутки

    except (Timeout, ConnectionError, KeyError, IndexError) as err:
        with open('logging.log', 'a') as file:
            file.write(f'\n{datetime.now()}, {type(err)}, search_hotels')
        return 'Вышло время запроса, или произошел сбой. Пожалуйста попробуйте еще раз!'
