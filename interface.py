import re
import psycopg2

import vk_api
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from core import VkTools

from config import acces_token, comunity_token


class BotInterface:
    def __init__(self, token: str, user: str, password: str):
        self.bot = vk_api.VkApi(token=token)
        self.user = user
        self.password = password
        self.result_users_photo = {}

    def create_db(self):
        conn = psycopg2.connect(
            database='listdb', user=self.user, password=self.password
        )
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS anketa(
                    id SERIAL PRIMARY KEY,
                    my_id INT NOT NULL,
                    ankets_id INT NOT NULL
                );
                """)
        return conn, cur

    def message_send(self, user_id: int, message: str, attachment=None):
        self.bot.method(
            'messages.send',
            {
                'user_id': user_id,
                'message': message,
                'random_id': get_random_id(),
                'attachment': attachment
            }
        )

    def append_result_users_photo(
            self, event_user_id: int, params_search: str
    ):
        tools = VkTools(acces_token)
        conn, cur = self.create_db()
        city_id, age_from, age_to, sex, relation = params_search.split(',')
        city_id = int(city_id)
        age_from = int(age_from)
        age_to = int(age_to)
        sex = int(sex)
        relation = int(relation)
        profiles = tools.user_serch(city_id, age_from, age_to, sex, relation)
        for profil in profiles:
            photo_the_user = []
            profile_info = tools.get_profile_info(profil['id'])
            if profile_info:
                if 'city' in profile_info[0]:
                    if profile_info[0]['city']['id'] == city_id:
                        user_id = profile_info[0]['id']
                        cur.execute(
                            "SELECT * FROM anketa WHERE ankets_id = %s;",
                            (user_id, )
                        )
                        if not cur.fetchall():
                            cur.execute(
                                "INSERT INTO anketa (my_id, ankets_id) \
                                    VALUES (%s, %s)",
                                (event_user_id, user_id, )
                            )
                            photos = tools.photos_get(user_id)
                            if photos:
                                for photo in photos:
                                    media = f"?z=photo{photo['owner_id']}_{photo['id']}"
                                    photo_the_user.append(media)
                if photo_the_user:
                    self.result_users_photo[profil['id']] = photo_the_user
        conn.commit()
        cur.close()
        conn.close()
        self.message_send(
            event_user_id,
            'Список фотографий собран. Для просмотра скажите "далее"'
        )

    def communication(self):
        longpull = VkLongPoll(self.bot)
        for event in longpull.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                event_text = event.text.lower()
                match = re.match(
                    r'поиск \d{1,3}\,\d{1,3}\,\d{1,3}\,[1|2]\,[0|1]',
                    event_text
                )
                if event_text == 'привет':
                    self.message_send(event.user_id, 'Добрый день')
                    self.message_send(
                        event.user_id,
                        'Для нового поиска напишите "поиск" пробел и через\
                              запятую укажите параметры поиска: id города,\
                                  возраст От, возраст До, пол(1 - женский,\
                                      2- мужской), семейное положение (0 -\
                                          холост, 1 - в браке)'
                    )
                    self.message_send(
                        event.user_id,
                        'Пример запроса:\nпоиск 99,20,40,2,1'
                    )
                elif match:
                    _, params_search = event_text.split(' ')
                    self.append_result_users_photo(
                        event.user_id, params_search
                    )
                elif event.text.lower() == 'далее':
                    if self.result_users_photo:
                        for id in self.result_users_photo.keys():
                            self.message_send(
                                event.user_id, f'https://vk.com/{id}'
                            )
                            for photo_user in self.result_users_photo[id]:
                                self.message_send(
                                    event.user_id,
                                    f'https://vk.com/{id}{photo_user}'
                                )
                            self.result_users_photo.pop(id, None)
                            break
                    else:
                        self.message_send(
                            event.user_id,
                            'Вы еще не запускали команду "поиск"'
                        )
                else:
                    self.message_send(
                        event.user_id,
                        'Для нового поиска напишите "поиск" пробел и через\
                              запятую укажите параметры поиска: id города,\
                                  возраст От, возраст До, пол(1 - женский,\
                                      2- мужской), семейное положение (0 -\
                                          холост, 1 - в браке)'
                    )
                    self.message_send(
                        event.user_id,
                        'Пример запроса:\nпоиск 99,20,40,2,1'
                    )
                    self.message_send(
                        event.user_id,
                        'Для просмотра уже собранного списка скажите "далее"'
                    )


def source_users():
    bot = BotInterface(comunity_token, 'postgres', 'Shcola219')
    bot.communication()


if __name__ == '__main__':
    source_users()
