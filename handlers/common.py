""" Взаимодействие с помощью команда
    /*****
    /start
"""
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from fsm import Menu
from db_func.db_function import DataBaseBot
from keyboards import get_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    db = DataBaseBot()  # Обращаемся к Базе данных
    db.count_user_plus(id_chat=message.chat.id)
    responsible_id = db.get_responsible_id()
    if message.chat.id == responsible_id[0]:
        await state.set_state(Menu.start_answer)
        await message.answer('Ожидаем сообщений от пользователей')
    else:
        await state.set_state(Menu.choice)  # Ставим состояние начала работы
        await state.update_data(identifier=1)  # Сохраняем текущий identifier

        chat_id = message.chat.id  # Записываем ID chat с пользователем

        help_count = db.get_count_help()  # Берем число людей которым помог бот

        list_id, list_button = db.get_buttons(1)
        text_msg, name_file, action = db.get_msg_text(1)
        await state.update_data(list_id=list_id)

        await message.answer(text=text_msg.format(help_count=help_count),
                             parse_mode='html')
        await message.answer(text="""<b>Как я устроен</b>
Я предложу вам готовые ответы на множество вопросов. Здесь содержится более 150 тематических рубрик, которые составлены на основе экспертных статей свыше 30 проверенных организаций.

🔸Навигация осуществляется с помощью кнопок, располагающихся под или над полем для ввода текста. 

🔸Обратите внимание, что мне нужно несколько секунд на размышления. Если нажали на кнопку, то дождитесь от меня ответа! 

🔸Если же я долго не отвечаю или завис - вам понадобится команда /start. Введите ее в текстовое поле для перезапуска нашего диалога.

Чем вы хотите помочь?""",
                             reply_markup=get_keyboard(list_button=list_button, list_id=list_id, chat_id=chat_id),
                             parse_mode='html')
