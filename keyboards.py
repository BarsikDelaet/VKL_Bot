from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from db_func.db_function import DataBaseBot


def get_keyboard(list_button, list_id, chat_id):
    """ Создание подстрочной клавиатуры(с доп. кнопкой если пользователь корректор)

    list_button[] - список кнопок

    list_id[] - список нумерации кнопок

    chat_id - число id пользователя
    """
    db = DataBaseBot()
    corrector_id = db.get_corrector_id()  # Для тех кто корректор создается кнопка ''Исправить текс 🖋'
    if chat_id in corrector_id:
        list_button.append('Исправить текс 🖋')
    n = len(list_id)
    for i in range(0, n):
        if list_button[i] == '📍Обратно в раздел':
            list_id.append(list_id.pop(i))
            list_button.append(list_button.pop(i))

    buttons = [
        [KeyboardButton(text=text) for text in list_button]
    ]
    # button_next = [[KeyboardButton(text=">>>")]]  # Кнопка для вывода остальных кнопок
    # if len(list_button) >= 10:  # TODO: Выглядит не оч, надо посмотреть как сделать лучше
    #     print(buttons[:9])
    #     buttons = buttons[:9]+button_next
    #     print(buttons)
    #     builder = ReplyKeyboardBuilder(buttons)
    #     builder.adjust(1)
    # else:
    builder = ReplyKeyboardBuilder(buttons)
    builder.adjust(1)

    keyboard = builder.as_markup(input_field_placeholder="Выбери кнопку 👇", resize_keyboard=True)
    return keyboard


# def get_next_keyboard(list_button, list_id, chat_id):
#     """ Создаем клавиатуру следующих кнопок """
#     db = DataBaseBot()
#     print(list_button)
#     corrector_id = db.get_corrector_id()  # Для тех кто корректор создается кнопка ''Исправить текс 🖋'
#     if chat_id in corrector_id:
#         list_button.append('Исправить текс 🖋')
#     n = len(list_id)
#     for i in range(0, n):
#         if list_button[i] == '📍Обратно в раздел':
#             list_id.append(list_id.pop(i))
#             list_button.append(list_button.pop(i))
#
#     buttons = [
#         [KeyboardButton(text=text) for text in list_button]
#     ]
#     button_back = [[KeyboardButton(text="<<<")]]  # Кнопка для вывода предыдущих кнопок
#     print(f"Второй набор  - {buttons}")
#     n = len(list_button)+1
#     print(buttons[0][9:])
#     buttons = buttons[9:n]+button_back
#     print(buttons)
#     builder = ReplyKeyboardBuilder(buttons)
#     builder.adjust(1)
#
#     keyboard = builder.as_markup(input_field_placeholder="Выбери кнопку 👇", resize_keyboard=True)
#     return keyboard


def get_inline_keyboard():
    """ Создание ин лайн клавиатуры для ответа пользователю. """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Ответить",
                                     callback_data='Answer'))
    return builder
