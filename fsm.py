""" Состояния бота для перехода по категориям. """
from aiogram.fsm.state import StatesGroup, State


class Menu(StatesGroup):
    """ Вывод и обработка меню. """
    choice = State()
    find_fund = State()
    feedback = State()
    find_city = State()
    start_answer = State()
    answer = State()
    correct_msg = State()
