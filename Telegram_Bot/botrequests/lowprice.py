import json
import requests
import emoji
import time
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


def search_hotels(count_hotels: str, date_1: str, date_2: str, id_city) -> None:
    try:

        def emoji_star(retings: int):
            ret = round(retings)
            if ret == 0:
                ret = "👎"
            elif ret == 1:
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

        quantity_data = int((date_2 - date_1).days)
        total_list = []
        count = 0
        for info in list_hotels:
            count += 1
            info_hotels: dict = {}
            for name in info:
                if name == "address":
                    info_hotels.update({"Адрес:": info["address"]["streetAddress"]})
                elif name == "name":
                    info_hotels.update({"Название отеля:": info["name"]})
                elif name == "ratePlan":
                    info_hotels.update({"Цена проживания в сутки:": info["ratePlan"]["price"]["current"]})
                    info_hotels.update({"Стоимость за время проживания:":
                                        str(round(float(info["ratePlan"]["price"]["exactCurrent"]) *
                                        int(quantity_data), 2)) + " RUB"})
                elif name == "starRating":
                    info_hotels.update({"Оценка:": emoji_star(info["starRating"])})
                elif name == "landmarks":
                    info_hotels.update({"Растояние до центра:": info['landmarks'][0]["distance"]})
                elif name == "id":
                    info_hotels.update({"Ссылка на отель:": f'hotels.com/ho{info["id"]}'})
            total_list.append(info_hotels)
            if count == int(count_hotels):
                break
        return total_list

    except (Timeout, ConnectionError, KeyError, IndexError) as err:
         with open('logging.log', 'a') as file:
            file.write(f'\n{datetime.now()}, {type(err)}, search_hotels')
         return 'Вышло время запроса, или произошел сбой. Пожалуйста попробуйте еще раз!'


def search_photo(count_user, id_hotel):
    try:
        querystring = {"id": id_hotel}
        response = requests.request("GET", url_photo, headers=headers, params=querystring)
        data = json.loads(response.text)
        result = data["hotelImages"]

        count = 0
        total_list = []
        for photo_url in result:
            count += 1
            photo = photo_url["baseUrl"].format(size="z")
            total_list.append(photo)
            if count == int(count_user):
                break

        return total_list

    except (Timeout, ConnectionError, KeyError, IndexError) as err:
        with open('logging.log', 'a') as file:
            file.write(f'\n{datetime.now()}, {type(err)}, search_photo')
        return 'Вышло время запроса, или произошел сбой. Пожалуйста попробуйте еще раз!'
