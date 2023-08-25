import requests
import datetime
import bs4
import re
import fake_headers
import vk_api
from db import show_fav_list, save_person, search_details_keyboard, save_data_keyboard, send, delete_list_of_fav
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

with open('token.txt', 'r') as file:
    token = file.read()
with open('standalone_token.txt', 'r') as file:
    token_2 = file.read()
with open('access_token.txt', 'r') as file:
    token_3 = file.read()
vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, 221977511)
vk = vk_session.get_api()
vk_session_app = vk_api.VkApi(token=token_2)
vk_session_user = vk_api.VkApi(token=token_3)

def calculate_age(born: str):
    today = datetime.date.today()
    splitted_born = born.split('.')
    return today.year - int(splitted_born[2]) - ((today.month, today.day) < (int(splitted_born[1]), int(splitted_born[0])))

def main():
    for number, event in enumerate(longpoll.listen()):
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
            message = event.object.message['text']
            message = re.sub(r'\[.*]\ (\w*)', r'\1', message).capitalize()
            user_id = event.obj.message['peer_id']
            if message == "Старт" or message == "Показать список команд":
                send(vk_session=vk_session, chat_id=user_id, message_text='Выбери функцию:\n Поиск кандидатов \n Показать список избранных \n Удалить избранные', keyboard=search_details_keyboard())
            elif message == "Очистить избранные":
                try:
                    delete_list_of_fav(user_id=user_id)
                    send(vk_session=vk_session, chat_id=user_id, message_text='Избранные удалены! \nВыбери функцию:\n Поиск кандидатов \n Показать список избранных', keyboard=search_details_keyboard())
                except vk_api.exceptions.ApiError [100]:
                    send(vk_session=vk_session, chat_id=user_id, message_text='Список избранных пуст \nВыбери функцию:\n Поиск кандидатов \n Показать список избранных', keyboard=search_details_keyboard())
            elif message == "Показать список избранных":
                show_fav_list(user_id=user_id, vk_session=vk_session)
            elif message == 'Поиск кандидатов' or message == "Продолжить поиск":
                person_id = event.message.from_id
                bdate = calculate_age(vk_session.method('users.get', {'user_ids':(person_id), 'fields':'bdate'})[0]['bdate'])
                home_town_id = vk_session.method('users.get', {'user_ids':(person_id), 'fields':'city'})[0]['city']['id']
                sex = vk_session.method('users.get', {'user_ids':(person_id), 'fields':'sex'})[0]['sex']
                if sex == 1:
                    sex = 2
                elif sex == 2:
                    sex = 1
                else:
                    sex = 0
                list_not_closed = [value for value in vk_session_user.method('users.search', {'sort':1, 'city_id': home_town_id, 'sex':sex, 'age_from': bdate-3, 'age_to':bdate+3, 'has_photo':1})['items'] if value['is_closed'] == False]
                item = list_not_closed[number]
                items = vk_session_app.method('photos.get', values={'owner_id':item['id'], 'extended':1, 'album_id':'profile'})['items']
                like_list = [likes_on_photo['likes']['count'] for likes_on_photo in items]                        
                photos_id = [photo['id'] for photo in items]
                photos_list = [f"photo{item['id']}_{photo[1]}" for photo in sorted(zip(like_list, photos_id), reverse=True)[:3]]
                attachment = ','.join(photos_list)
                photo_link_list = []
                send(vk_session=vk_session, chat_id=user_id, message_text=f'{item["first_name"]} {item["last_name"]}, https://vk.com/id{item["id"]}', attachment=attachment, keyboard=save_data_keyboard())
                send(vk_session=vk_session, chat_id=user_id, message_text='Сохранить пользователя в избранные?')
                for event in longpoll.listen():
                    if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
                        message = event.object.message['text']
                        message = re.sub(r'\[.*]\ (\w*)', r'\1', message).capitalize()
                        if message == 'Да':
                            save_person(vk_session=vk_session, name=f'{item["first_name"]} {item["last_name"]}', link=f'https://vk.com//{item["id"]}', photos_link=photos_list, user=item["id"], index=number+1, chat_id=user_id)
                        break
                send(vk_session=vk_session, chat_id=user_id, message_text='Выбери функцию:\n Поиск кандидатов \n Показать список избранных \n Удалить избранные', keyboard=search_details_keyboard())
                        

if __name__ == '__main__':
    main()          