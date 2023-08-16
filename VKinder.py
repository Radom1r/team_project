import json
import os
import requests
import datetime
import shutil
import bs4
import fake_headers
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from models import *
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
 
with open('token.txt', 'r') as file:
    token = file.read()
with open('standalone_token.txt', 'r') as file:
    token_2 = file.read()
vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, 221977511)
vk = vk_session.get_api()
vk_session_app = vk_api.VkApi(token=token_2)

def send(chat_id, message_text, attachment=''):
    message = {
        'chat_id': chat_id,
        'message': message_text,
        'random_id': 0, 
        'attachment': attachment
    }
    vk_session.method('messages.send', message)

def calculate_age(born: str):
    today = datetime.date.today()
    splitted_born = born.split('.')
    return today.year - int(splitted_born[2]) - ((today.month, today.day) < (int(splitted_born[1]), int(splitted_born[0])))

def save_person(session, name, link, photos_link, user, index, chat_id):
    try:
        profile_link = Profile_link(profile_link=link, profile_link_id=index)
        session.add(profile_link)
        session.commit()
        name = Name(name_and_surname=name, profile_link_id=index)
        session.add(name)
        for photo in photos_link:
            photo = Photo_links(photo_link=f'photo_{user}_{photo}', profile_link_id=index)
            session.add(photo)
        session.commit()
    except sq.exc.IntegrityError:
        send(chat_id, "Данный пользователь уже сохранен в избранные")
        session.rollback()
    except:
        print('Возникла непредвиденная ошибка, попробуйте еще раз')

def main():
    index = 0
    for event in longpoll.listen():
        chat_id = event.chat_id
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.from_chat:
                message = event.object.message['text'].capitalize()
                if message == "Старт":
                    send(chat_id, 'Выбери функцию:\n Поиск кандидатов \n Показать список избранных')
                elif message == "Показать список избранных":
                    DNS = 'postgresql://user123:myPassword@localhost:5432/team_project'
                    engine = sq.create_engine(DNS, pool_size=20)
                    Session = sessionmaker(bind=engine)
                    session = Session()
                    list_od_favorites = session.query(Profile_link.profile_link, Name.name_and_surname).filter(Profile_link.profile_link_id == Name.profile_link_id).all()
                    all_list = [f'{number+1}) {value[1]}, {value[0]} \n' for number, value in enumerate(list_od_favorites)]
                    send(chat_id, ''.join(all_list))
                    send(chat_id, 'Выберите следующую функцию: \n Поиск кандидатов \n Показать список избранных')
                    session.close()
                elif message == 'Поиск кандидатов' or message == "Да":
                    user_id = event.message.from_id
                    bdate = calculate_age(vk_session.method('users.get', {'user_ids':(user_id), 'fields':'bdate'})[0]['bdate'])
                    home_town_id = vk_session.method('users.get', {'user_ids':(user_id), 'fields':'city'})[0]['city']['id']
                    sex = vk_session.method('users.get', {'user_ids':(user_id), 'fields':'sex'})[0]['sex']
                    if sex == 1:
                        sex = 2
                    elif sex == 2:
                        sex = 1
                    else:
                        sex = 0
                    headers = fake_headers.Headers().generate()
                    search_link = f'https://vk.com/search?c%5Bage_from%5D={bdate-3}&c%5Bage_to%5D=sex{bdate-3}&c%5Bcity%5D={home_town_id}&c%5Bname%5D=1&c%5Bper_page%5D=40&c%5Bphoto%5D=1&c%5Bsection%5D=people&c%5Bsex%5D={sex}'
                    response = requests.get((search_link), headers=headers, timeout=100).content
                    soup = bs4.BeautifulSoup(response, 'lxml')
                    names = soup.find_all('div', class_='labeled name')
                    list_of_names = [name.find('a', onclick="return nav.go(this, event);").text for name in names]
                    list_of_links = [name.find('a', onclick="return nav.go(this, event);")['href'] for name in names]
                    shorten_name = list_of_links[index][1:]
                    user = vk_session.method('utils.resolveScreenName', values={'screen_name':shorten_name})['object_id']
                    items = vk_session_app.method('photos.get', values={'owner_id':user, 'extended':1, 'album_id':'profile'})['items']
                    like_list = [likes_on_photo['likes']['count'] for likes_on_photo in items]                        
                    photos_id = [photo['id'] for photo in items]
                    photos_list = [photo[1] for photo in sorted(zip(like_list, photos_id), reverse=True)[:3]]
                    photo_link_list = []
                    send(chat_id, f'{list_of_names[index]}, https://vk.com{list_of_links[index]}', attachment=f'photo{user}_{photos_list[0]},photo{user}_{photos_list[1]},photo{user}_{photos_list[2]}')
                    send(chat_id, 'Хочешь посмотреть следующего? Напиши "Да" для продолжения или "Сохранить" для сохранения кандидата в избранные')
                    for event in longpoll.listen():
                        chat_id = event.chat_id
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            if event.from_chat:
                                message = event.object.message['text'].capitalize()
                                if message == 'Сохранить':
                                    DNS = 'postgresql://user123:myPassword@localhost:5432/team_project'
                                    engine = sq.create_engine(DNS, pool_size=20)
                                    Session = sessionmaker(bind=engine)
                                    session = Session()
                                    save_person(session=session, name=list_of_names[index], link=f'https://vk.com{list_of_links[index]}', photos_link=photos_list, user=user, index=index+1, chat_id=chat_id)
                                    send(chat_id, 'Хочешь посмотреть следующего? Напиши "Да" для продолжения')
                                    session.close()
                                break
                    index += 1
if __name__ == '__main__':
    main()          


# keyboard = VkKeyboard(one_time=True)
# keyboard.add_callback_button(label='Привет', color=VkKeyboardColor.NEGATIVE, payload={'type':'show_snackbar', 'text':'uygtyrtc'})
# keyboard.add_button('Клавиатура', color=VkKeyboardColor.POSITIVE)
# keyboard.add_line()
# keyboard.add_location_button()
# keyboard.add_line()

# for event in longpoll.listen():
#     user_id = event.object.message['from_id']
#     print(user_id)
#     if event.type == VkBotEventType.MESSAGE_NEW:
#         if event.from_chat:
#             chat_id = event.chat_id
#             keyboard = {  
#    "one_time":True,
#    'chat_id':chat_id,
#    'random_id' : 1,
#    "buttons":[  
#       [  
#          {  
#             "action":{  
#                "type":"location",
#                "payload":"{\"button\": \"1\"}"
#             }
#          }
#       ]
#    ]
# }
#             message = event.object.message['text'].lower()
#             if event.object.payload.get('type') == 'show_snackbar':
#                 vk.messages.sendMessageEventAnswer(event_id=event.object.event_id, user_id=event.object.user_id, peer_id=event.object.peer_id, event_data=keyboard)
#             else:
#                 break