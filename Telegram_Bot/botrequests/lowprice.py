import json
import requests
import emoji
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


def search_hotels(id_city: str, date_1: str, date_2: str) -> None:
    try:

        def emoji_star(retings):
            ret = round(retings)
            if ret == 1:
                ret = emoji.emojize(":star:")
            elif ret == 2:
                ret = emoji.emojize(":star:" * 2)
            elif ret == 3:
                ret = emoji.emojize(":star:" * 3)
            elif ret == 4:
                ret = emoji.emojize(":star:" * 4)
            elif ret == 5:
                ret = emoji.emojize(":star:" * 5)
            return ret

        querystring = {"destinationId": id_city, "locale": "ru_RU", "currency": "RUB", "checkIn": date_1, "checkOut": date_2}
        response = requests.request("GET", url_hotels, headers=headers, params=querystring, timeout=15)
        data = json.loads(response.text)
        list_hotels = data["data"]["body"]["searchResults"]["results"]
        total_list = []
        for info in list_hotels:
            id_hotel, name_hotel, address, ratings, city, price = str(info["id"]), info["name"], \
                                                    info["address"]["streetAddress"], info["starRating"], \
                                                    info["address"]["locality"], info["ratePlan"]["price"]["current"]
            rating = emoji_star(ratings)
            info_hotels = [id_hotel, name_hotel, address, ratings, city, price]
            total_list.append(info_hotels)
        return total_list

            # Центр города
            # Цена за вермя проживания ?
            # Цена за сутки ?

    except (Timeout, ConnectionError, KeyError, IndexError) as err:
         with open('logging.log', 'a') as file:
            file.write(f'\n{datetime.now()}, {type(err)}, search_hotels')
         return 'Вышло время запроса, или произошел сбой. Пожалуйста попробуйте еще раз!'


def search_photo(id_hotel):
    try:
        querystring = {"id": id_hotel}

        headers = {
            "X-RapidAPI-Key": "92df29d080msh46023caec8bbfe1p16ec82jsn566f363513e0",
            "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)


    except (Timeout, ConnectionError, KeyError, IndexError) as err:
         with open('logging.log', 'a') as file:
            file.write(f'\n{datetime.now()}, {type(err)}, search_photo')
         return 'Вышло время запроса, или произошел сбой. Пожалуйста попробуйте еще раз!'
