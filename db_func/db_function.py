import datetime

import psycopg2
from db_func.config import *


class DataBaseBot:

    def __init__(self):
        """Подключение к БД"""
        self.connect = psycopg2.connect(
            database=DATABASE,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT
        )

    def get_msg_text(self, identifier):
        """ Получает id кнопки.

        Возвращает 3 списка данных: text_msg, file_path, action


        text_msg[] - Текст кнопки | None

        file_path[] - Путь к файлу | None

        action[] - Название действия | None"""
        cursor = self.connect.cursor()
        cursor.execute(f"""
            select answer_text, name_file, action
            from node
            where identifier = '{identifier}'""")
        msg = cursor.fetchone()
        return msg

    def get_corrector_id(self):
        """ Получить id корректора. """
        cursor = self.connect.cursor()
        cursor.execute("""
            select id
            from corrector_id""")
        count = cursor.fetchall()
        count = [i[0] for i in count]
        return count

    def get_responsible_id(self):
        """ Получить id отвечающего. """
        cursor = self.connect.cursor()
        cursor.execute("""
            select id
            from responsible_id""")
        count = cursor.fetchall()
        count = [i[0] for i in count]
        return count

    def update_text(self,  msg, identifier):
        """ Меняет текст  """
        cursor = self.connect.cursor()
        cursor.execute(f"""
            Update node SET answer_text = '{msg}'
            Where identifier = {identifier}
        """)

    def get_buttons(self, identifier):
        """ Получает id кнопки, возвращая 2 списка:

        list_id[] - список id кнопок

        list_button[] - список с названием кнопок"""
        cursor = self.connect.cursor()
        cursor.execute(f"""
            select identifier, button_text
            from node
            where identifier in (
            select dest_node
            from link
            where source_node = {identifier})
            order by identifier""")
        list_button = cursor.fetchall()
        return [i[0] for i in list_button], [i[1] for i in list_button]

    def get_identifier(self, button_text):
        """ Получает название кнопки.(button_text)

         Возвращает её identifier"""
        cursor = self.connect.cursor()
        cursor.execute(f"""
                Select identifier
                From node
                Where button_text = '{button_text}'""")
        section = cursor.fetchall()
        if section is None:
            return 2
        else:
            section = [i[0] for i in section]
            return section

    def get_mail_data(self):
        """ Возвращает список разделов """
        cursor = self.connect.cursor()
        cursor.execute(f"""
                select name_mail, password_mail
                from mail""")
        data_mail = cursor.fetchone()
        return data_mail[0], data_mail[1]

    def len_cards(self):
        """ Возвращает кол-во карточек в БД """
        cursor = self.connect.cursor()
        cursor.execute(f"""
                select count(*)
                from cards""")
        count = cursor.fetchone()
        return count[0]

    def link_cards(self, id_card):
        """ Возвращает карточку по номеру """
        cursor = self.connect.cursor()
        cursor.execute(f"""
                select link_card
                from cards
                where id_card = {id_card}""")
        count = cursor.fetchone()
        return count[0]

    def path_cards_by_name(self, file_path: list):
        """ Возвращает список списков линков карточек по названию или pdf"""
        link_cards = []
        for name in file_path:
            cursor = self.connect.cursor()
            cursor.execute(f"""
                    select link_card from cards
                    where name_card = '{name}'""")
            link_cards.append(cursor.fetchone()[0])
        return link_cards

    def get_items(self, identifier):
        """ Получает название подраздела выше кнопки 'адреса в моем городе' """
        cursor = self.connect.cursor()
        cursor.execute(f"""
                select button_text
                from node
                where identifier = {identifier}""")
        items = cursor.fetchone()
        return items[0]

    def get_admin_id(self):
        """ Возвращает id админа """
        cursor = self.connect.cursor()
        cursor.execute(f"""
                        select *
                        from admin_id""")
        items = cursor.fetchone()
        return items[0]

    def count_help_plus(self, id_chat):
        """ Добавляет знание +1 за нажатие кнопки. """
        cursor = self.connect.cursor()
        cursor.execute(f"""
            select * from count_help
            where help = '{id_chat}'""")
        check = cursor.fetchone()
        if check:
            return
        else:
            cursor = self.connect.cursor()
            cursor.execute(f"""
                        insert into count_help(help)
                        Values('{id_chat}')""")
            return

    def get_count_help(self):
        """ Возвращает кол-во человек кому помог """
        cursor = self.connect.cursor()
        cursor.execute(f"""
                   select count(*) from count_help""")
        count = cursor.fetchone()
        return count[0]

    def count_user_plus(self, id_chat):
        """ Добавляет нового пользователя.
         Дату его первого захода"""
        cursor = self.connect.cursor()
        cursor.execute(f"""
            select * from count_user
            where id_user = '{id_chat}'""")
        check = cursor.fetchone()
        if check:
            return
        else:
            date = datetime.date.today().strftime('%Y-%m-%d')
            cursor = self.connect.cursor()
            cursor.execute(f"""
                        insert into count_user(id_user, last_visit, count_visit, first_visit)
                        Values('{id_chat}', '{date}', {1}, '{date}')""")
            return

    def get_random_text(self, random_num):
        """ Возвращает текст с переданным номером """
        cursor = self.connect.cursor()
        cursor.execute(f"""
        select answer_text 
        from random_text
        where id_text = {random_num}""")
        count = cursor.fetchone()
        return count[0]

    def update_last_visit(self, chat_id):  # TODO
        """ Записывает новую дату посещения пользователя и добавляет +1 к посещению если последнее посещение
         было в другой день"""
        cursor = self.connect.cursor()
        cursor.execute(f"""
        Select last_visit 
        from count_user
        where id_user = '{chat_id}'""")
        date = cursor.fetchone()
        date = date[0]
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')
        if date == now_date:
            return
        else:
            cursor.execute(f"""
            Update count_user
            set last_visit = '{now_date}',
            count_visit = count_visit+1
            where id_user = '{chat_id}'""")

    def count_click_button(self, button_id: int):
        """ Считает кол-во нажатых кнопок по id кнопки. """
        cursor = self.connect.cursor()
        cursor.execute(f"""
        update count_click_button
        set number_of_click = number_of_click+1
        where button_id = {button_id}""")

    def __del__(self):
        self.connect.commit()
        self.connect.close()
