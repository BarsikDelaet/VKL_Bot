""" Основные функции бота и переход по меню
"""
import time

import requests
import random
import os
from bs4 import BeautifulSoup

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from fsm import Menu
from config import API_TOKEN
from db_func.db_function import DataBaseBot
from keyboards import get_keyboard, get_inline_keyboard  # , get_next_keyboard

router = Router()

bot = Bot(token=API_TOKEN)


@router.message(Menu.choice, F.text)
async def menu(message: types.Message, state: FSMContext):
    """ Обработка сообщения с раздела меню. """
    chat_id = message.chat.id  # ID-пользователя
    button_text = message.text  # Название нажатой кнопки
    db = DataBaseBot()
    db.update_last_visit(chat_id=chat_id)  # Счетчик кол-во посещений

    data = await state.get_data()  # Получаем список сохраненных данных
    back_id = data['identifier']  # Получаем родительский identifier

    if button_text == 'Нашлось все, что нужно':  # Увеличиваем счетчик людей которым помогли
        db.count_help_plus(chat_id)

    msg_id = db.get_identifier(button_text)  # Получение id выбранной кнопки
    if not msg_id:  # Если сообщение нет в списке возможных(имеет id 2)
        list_id, list_button = db.get_buttons(identifier=back_id)  # Список кнопок по выбранной кнопке
        text_msg, file_path, action = db.get_msg_text(2)  # Получаем данные данной кнопки
        await message.answer(text=text_msg,  # Отправляем сообщение о неверном выборе кнопки
                             reply_markup=get_keyboard(list_button=list_button, list_id=list_id, chat_id=chat_id),
                             parse_mode='html')

    elif button_text == 'Исправить текс 🖋':  # Исправление сообщения
        await state.set_state(Menu.correct_msg)
        text_msg, file_path, action = db.get_msg_text(back_id)  # Получаем данные выбранной кнопки
        await message.answer(text='Скопируйте текст, исправьте его и отправьте исправленную версию')
        time.sleep(1)
        await message.answer(text=text_msg, reply_markup=types.ReplyKeyboardRemove())
        
    else:
        list_id = data['list_id']
        if len(list_id) == 0:
            list_id.append(msg_id[0])
        for id_node in msg_id:  # Выбор правильного id
            if id_node in list_id:
                msg_id = id_node
                break

    db.count_click_button(button_id=msg_id)  # Считает кол-во нажатий на кнопку

    await state.update_data(back_identifier=back_id)
    await state.update_data(identifier=msg_id)

    list_id, list_button = db.get_buttons(identifier=msg_id)  # Список кнопок по выбранной кнопке
    text_msg, file_path, action = db.get_msg_text(msg_id)  # Получаем данные данной кнопки
    await state.update_data(list_id=list_id)
    data1 = await state.get_data()

    if not action:  # Если активности нет
        text = text_processing(text_msg)
        for text_msg in text:
            await message.answer(text=text_msg.format(help_count=db.get_count_help()),
                                 reply_markup=get_keyboard(list_button=list_button, list_id=list_id,
                                                           chat_id=chat_id),
                                 disable_web_page_preview=True,
                                 parse_mode='html')

    match action:
        case 'send_organizers':  # Оставили предложение с обратной связью
            text = text_processing(text_msg)
            list_id, list_button = db.get_buttons(identifier=1)

            await state.update_data(subject=button_text)
            await state.update_data(list_id=list_id)
            await state.set_state(Menu.feedback)

            for text_msg in text:
                await message.answer(text=text_msg,
                                     reply_markup=get_keyboard(['🏛Главное меню'],
                                                               [1],
                                                               0000000),
                                     disable_web_page_preview=True,
                                     parse_mode='html')
        case 'search_in_city':  # TODO: Поиск города
            await state.set_state(Menu.find_city)
            text = text_processing(text_msg)
            for text_msg in text:
                await message.answer(text=text_msg,
                                     reply_markup=types.ReplyKeyboardRemove(),
                                     disable_web_page_preview=True,
                                     parse_mode='html')
        case '':  # TODO: Оставили отзыв с обратной связью
            pass
        case 'send_file':  # Отправляет файл
            if text_msg:  # Если есть текст выводим
                text = text_processing(text_msg)  # Список из текста
                for text_msg in text:  # Поочередный вывод сообщения без клавиатуры
                    await message.answer(text=text_msg,
                                         reply_markup=types.ReplyKeyboardRemove(),
                                         disable_web_page_preview=True,
                                         parse_mode='html')

            if '|' in file_path:  # Разделяем путь до файлов если фоток несколько
                file_path = file_path.split('|')
            else:
                file_path = [file_path]
            path_cards = db.path_cards_by_name(file_path=file_path)  # Список списков ссылок на карточки

            for path_card in path_cards:
                for link in path_card.split('|'):
                    photo = FSInputFile(path='data/photo/' + link)
                    await message.answer_photo(photo=photo,
                                               reply_markup=get_keyboard(list_button=list_button, chat_id=chat_id,
                                                                         list_id=list_id))
        case 'send_pdf':  # Отправка файла pdf
            text = text_processing(text_msg)  # Возвращаем список текстов
            for text_msg in text:  # Поочередно отправляем сообщения из списка
                await message.answer(text=text_msg,
                                     reply_markup=types.ReplyKeyboardRemove(),
                                     disable_web_page_preview=True,
                                     parse_mode='html')
            if '|' in file_path:  # Делим название файла, если надо или делаем списком, если одно название
                file_path = file_path.split('|')
            else:
                file_path = [file_path]

            for name in file_path:  # Отправляем файл с кнопками
                # with open('data/' + name, "rb") as pdf1:
                #     f1 = pdf1.read()
                file = FSInputFile(path='data/' + name)
                await message.answer_document(document=file,
                                              visible_file_name=name,
                                              reply_markup=get_keyboard(list_button=list_button,
                                                                        list_id=list_id, chat_id=chat_id))
        case 'search_fund':  # TODO: Поиск организации
            text = text_processing(text_msg)
            await state.set_state(Menu.find_fund)

            for text_msg in text:
                await message.answer(text=text_msg,
                                     reply_markup=types.ReplyKeyboardRemove(),
                                     disable_web_page_preview=True,
                                     parse_mode='html')
        case 'send_card_and_text':  # TODO: Случайный совет
            random_num = random.randint(1, 7)  # Получаем случайное число по кол-ву возможных советов
            text_msg = db.get_random_text(random_num)  # Получаем текст
            list_id, list_button = db.get_buttons(1)  # Кнопки для меню

            text = text_processing(text_msg)  # Обработка текста

            for text_msg in text:  # Выводим текст поочередно
                await message.answer(text=text_msg,
                                     reply_markup=get_keyboard(list_button=list_button,
                                                               list_id=list_id, chat_id=chat_id),
                                     disable_web_page_preview=True,
                                     parse_mode='html')
        case 'send_advice':
            count_cards = db.len_cards()  # Получаем кол-во карточек
            number = random.randint(1, count_cards)
            link_cards = db.link_cards(number)

            list_id, list_button = db.get_buttons(1)
            link_cards = link_cards.split('|')
            for link in link_cards[:-1]:
                photo = FSInputFile(path='data/photo/' + link)
                await message.answer_photo(photo=photo,
                                           reply_markup=types.ReplyKeyboardRemove())
            photo = FSInputFile(path='data/photo/' + link_cards[-1])
            await message.answer_photo(photo=photo,
                                       reply_markup=get_keyboard(list_button=list_button,
                                                                 list_id=list_id, chat_id=chat_id))


def text_processing(text):
    """ Обрабатывает текст - меняет все кавычки """
    text = text.replace('“', '"').replace('”', '"')

    if text.find('РАЗДЕЛИТЬ') + 1:  # Если в строке есть разделитель
        correct_text = []
        while text.find('РАЗДЕЛИТЬ') + 1:
            separator = text.find('РАЗДЕЛИТЬ')
            correct_text.append(text[:separator])
            text = text[separator + 10:]
        correct_text.append(text[:])
        return correct_text
    elif len(text) > 4096:
        index_separator = text.index('\n', 4000)
        return text[:index_separator], text[index_separator + 2:]
    text = [text]
    return text


@router.message(Menu.find_fund, F.text)
async def search_fund(message: types.Message, state: FSMContext):
    """ Проверяет организацию через известные источники """
    db = DataBaseBot()
    chat_id = message.chat.id
    await state.set_state(Menu.choice)

    status = find_fund(message.text)  # Отправка названия фонда на проверку

    list_id, list_button = db.get_buttons(identifier=123)  # Получаем название кнопок клавиатуры
    await state.update_data(identifier=123)
    if status:  # Отправка в зависимости от результата

        await message.answer(text="""Я нашел эту организацию в списке проверенных фондов у нашего партнера - сервиса <a href="https://dobro.mail.ru/sos/">VK Добро</a>. Все организации в их базе прошли серьезную проверку юристов и экспертов, предоставили документы и отчеты. Эти организации работают с соблюдением принципов открытости информации. 

Однако, в базе всего несколько сотен организации. А в стране их несколько сотен тысяч. Так что точно есть много отличных организаций, кто пока сюда не попал.
""", disable_web_page_preview=True,
                             reply_markup=get_keyboard(list_button=list_button, list_id=list_id, chat_id=0),
                             parse_mode='html')
    else:
        await message.answer(text="""Я не нашел эту организацию в списке проверенных фондов у нашего партнера <a href="https://dobro.mail.ru/sos/">VK Добро</a>. Это может быть хорошая организация, просто ее нет в базе сервиса. Хотите, я расскажу, по каким еще источникам можно ее проверить?

Например, во многих мобильных приложениях банков и у социального проекта Яндекса <a href="https://help.yandex.ru/">«Помощь рядом»</a> тоже есть списки проверенных фондов. Там вы можете посмотреть организации самостоятельно.

Организации, внесенные в эти базы, прошли специальную проверку и работают с соблюдением принципов открытости информации.
""",
                             disable_web_page_preview=True,
                             reply_markup=types.ReplyKeyboardRemove(),
                             parse_mode='html')
        for link in "Кто такие мошенники 1.jpg|Кто такие мошенники 2.jpg".split('|'):
            photo = FSInputFile('data/photo/' + link)
            await message.answer_photo(photo=photo,
                                       reply_markup=get_keyboard(list_button=list_button,
                                                                 list_id=list_id, chat_id=0))


def find_fund(name_fond):
    """ Поиск фондов и организаций по названию"""
    results = []
    name_fond_plus = '+'.join(name_fond.split())  # Парсим название
    response = requests.get(f'https://dobro.mail.ru/sos/?query={name_fond_plus}')
    contents = response.text
    bs = BeautifulSoup(contents, 'lxml')
    address = bs.find_all('span', class_='vkuiVisuallyHidden')

    for name in address:
        results.append(name.text.lower())
    name_fond = name_fond.lower()
    if name_fond in results:  # Отправка результата нашлось/не нашлось
        return True
    else:
        return False


@router.message(Menu.feedback, F.text)
async def send_admin(message: types.Message, state: FSMContext):
    """ Отправляет сообщение на тг аккаунт """
    db = DataBaseBot()
    data = await state.get_data()
    await state.set_state(Menu.choice)

    list_id, list_button = db.get_buttons(1)

    chat_id = message.chat.id  # id пользователя, который отправляет запрос
    subject = data['subject']  # Получаем раздел из которого идет запрос
    if message.text == "🏛Главное меню":
        text_msg, file_path, action = db.get_msg_text(1)
        help_count = db.get_count_help()
        await message.answer(text=text_msg.format(help_count=help_count),
                             reply_markup=get_keyboard(list_button=list_button, list_id=list_id, chat_id=0))
    else:
        responsible_id = db.get_responsible_id()  # id кому отправлять

        text_from_admin = f'ID пользователя: {str(chat_id)}\nРаздел: {subject}\n\nСообщение: {message.text}'  # Формирования сообщения для отправки
        await bot.send_message(chat_id=responsible_id[0], text=text_from_admin,
                               reply_markup=get_inline_keyboard().as_markup())
        if subject == "Оставить отзыв":  # Если оставляют отзыв
            await message.answer(text="""Спасибо, что нашли время оставить отзыв.
    
Если хотите продолжить дальше, выберите интересующий пункт.""",
                                 reply_markup=get_keyboard(list_button=list_button, list_id=list_id, chat_id=0))
        else:
            await message.answer(text="""Спасибо, ответим Вам в течение 24 часов, если вопрос поступил в рабочее время.
    
Если хотите продолжить дальше, выберите интересующий пункт.
    """,
                                 reply_markup=get_keyboard(list_button=list_button, list_id=list_id, chat_id=0))


@router.callback_query(Menu.start_answer, F.data.in_({'Answer': 'Ответить'}))
async def get_answer(call: types.CallbackQuery, state: FSMContext):
    """ Читаем сообщения ответа """
    await state.set_state(Menu.answer)
    text_msg = call.message.text.split('\n')
    id_user, team = text_msg[0].split(' ')[2], ' '.join(text_msg[1].split(': ')[1:])
    await call.message.answer(text=f"""Скопируйте ID и раздел: \n{id_user}\n{team}\n\nИ отправь сообщение разделив скопированное и ответ Enter-ом""",
                              reply_markup=types.ReplyKeyboardRemove())


@router.message(Menu.answer, F.text)
async def send_answer(message: types.Message, state: FSMContext):
    """ Отправляем ответ пользователю """
    await state.set_state(Menu.start_answer)
    text = message.text.split('\n')
    id_user = text[0]
    team = text[1]
    text = '\n'.join(text[2:])

    await bot.send_message(chat_id=id_user, text=f"""Вам пришел ответ от менеджера чат-бота: {team}\n\n{text}""")
    await message.answer('Сообщение отправлено')


@router.message(Menu.find_city, F.text)
async def search_in_city(message: types.Message, state: FSMContext):
    """ Функция поиска в городах. """
    db = DataBaseBot()
    await state.set_state(Menu.choice)
    data = await state.get_data()
    back_id = data['back_identifier']
    items = db.get_items(back_id)
    rus_items = {
        "Одежда детская или взрослая👕": "одежды",
        "Детские игрушки🧸": "игрушек",
        "Техника📻": "техники",
        "Книга: отдать другим или в макулатуру?📚": "книг"
    }
    result = find_in_city(city=message.text, items=rus_items[items])

    list_id, list_button = db.get_buttons(24)
    if 1 < len(result):
        result.append(' ')
        result.append(' ')

        await message.answer(f"""Вот варианты, которые нашел я.
Вы можете поискать адреса самостоятельно по картам (<a href="https://yandex.ru/maps/">«Яндекс.Карты»</a>, <a href="https://2gis.ru/">«2ГИС»</a>) с помощью ключевых слов, например: «благотворительный фонд», «благотворительный магазин», «социальный центр», «сдать» (технику, одежду, книги, пластик) и похожим.\n\n
{result[0]}
{result[1]}
{result[2]}
""",
                             reply_markup=get_keyboard(list_button=list_button, list_id=list_id, chat_id=0),
                             parse_mode='html')
    elif len(result) == 0:
        await message.answer(f"""К сожалению, в вашем городе я не смог найти варианты.
Вы можете поискать адреса самостоятельно по картам (<a href="https://yandex.ru/maps/">«Яндекс.Карты»</a>, <a href="https://2gis.ru/">«2ГИС»</a>) с помощью ключевых слов, например: «благотворительный фонд», «благотворительный магазин», «социальный центр», «сдать» (технику, одежду, книги, пластик) и похожим.""",
                             reply_markup=get_keyboard(list_button=list_button, list_id=list_id, chat_id=0),
                             parse_mode='html')


def find_in_city(city, items):  # TODO: переделать поиск
    """ Поиск адресов в городе """
    result = []
    # TODO: перевести город на английский
    response = requests.get(f'https://yandex.ru/maps/10945/uhta/search/пункт%20приёма%20{items}%20в%20городе%20{city}')
    contents = response.text
    bs = BeautifulSoup(contents, 'lxml')
    address = bs.find_all('a', 'search-business-snippet-view__address')

    for name in address:
        result.append(name.text)

    return result


# @router.message(Menu.correct_msg, F.text)
# def give_message_corrector(msg):
#     """ Обработка всех сообщений для корректирования текста. """
#     chat_id = msg.chat.id
#     db = DataBaseBot()
#     db.update_text(msg=msg.text, identifier=identifier[])