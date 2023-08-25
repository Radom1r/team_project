import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from models import *
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def search_details_keyboard():
    """
    Returns simplified main menu after missed user personal info collecting process.
    :return: dict (keyboard)
    """
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(label="Поиск кандидатов", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button(label="Показать список избранных", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button(label="Показать список команд", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button(label="Очистить избранные", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def save_data_keyboard():
    """
    Returns simplified main menu after missed user personal info collecting process.
    :return: dict (keyboard)
    """
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(label="Да", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button(label="Нет", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def send(vk_session, chat_id, message_text='', attachment='', keyboard=''):
    message = {
        'peer_id': chat_id,
        'message': message_text,
        'random_id': get_random_id(),
        'attachment': attachment,
        'keyboard': keyboard
        }
    vk_session.method('messages.send', message)

def save_person(vk_session, name, link, photos_link, user, index, chat_id):
    try:
        DNS = 'postgresql://postgres:postgres@localhost:5432/team_project'
        engine = sq.create_engine(DNS, pool_size=20)
        Session = sessionmaker(bind=engine)
        session = Session()
        profile_link = Profile_link(profile_link=link, profile_link_id=index)
        session.add(profile_link)
        session.commit()
        name = Name(name_and_surname=name, profile_link_id=index)
        session.add(name)
        for photo in photos_link:
            photo = Photo_links(photo_link=f'photo_{user}_{photo}', profile_link_id=index)
            session.add(photo)
        session.commit()
        session.close()
    except sq.exc.IntegrityError:
        send(vk_session, chat_id, "Данный пользователь уже сохранен в избранные")
        session.rollback()
        session.close()
    except:
        send(vk_session, chat_id, 'Возникла непредвиденная ошибка, попробуйте еще раз')

def show_fav_list(vk_session, user_id):
    DNS = 'postgresql://postgres:postgres@localhost:5432/team_project'
    engine = sq.create_engine(DNS, pool_size=20)
    Session = sessionmaker(bind=engine)
    session = Session()
    list_of_favorites = session.query(Profile_link.profile_link, Name.name_and_surname).filter(Profile_link.profile_link_id == Name.profile_link_id).all()
    all_list = [f'{number+1}) {value[1]}, {value[0]} \n' for number, value in enumerate(list_of_favorites)]
    send(vk_session=vk_session, chat_id=user_id, message_text=''.join(all_list))
    send(vk_session=vk_session, chat_id=user_id, message_text='Выбери функцию:\n Поиск кандидатов \n Показать список избранных', keyboard=search_details_keyboard())
    session.close()

def delete_list_of_fav(user_id):
    DNS = 'postgresql://postgres:postgres@localhost:5432/team_project'
    engine = sq.create_engine(DNS, pool_size=20)
    create_tables(engine)