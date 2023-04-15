import vk_api
import vk_api.exceptions
from vk_api.exceptions import ApiError


class VkTools:
    def __init__(self, token: str):
        self.ext_api = vk_api.VkApi(token=token)

    def get_profile_info(self, user_id):
        try:
            info = self.ext_api.method(
                'users.get',
                {'user_id': user_id, 'fields': 'bdate, city, sex, relation'}
            )
        except ApiError as error:
            print(error)
            return None

        return info

    def photos_get(self, user_id: int):
        photos = self.ext_api.method('photos.get',
                                     {'album_id': 'profile',
                                      'owner_id': user_id,
                                      'extended': 1,
                                      }
                                     )
        try:
            photos = photos['items']
        except KeyError:
            return

        result = []
        photos = sorted(
            photos,
            key=lambda k: k['likes']['count']+k['comments']['count'],
            reverse=True
        )
        for num, photo in enumerate(photos):
            result.append(
                {
                    'owner_id': photo['owner_id'],
                    'id': photo['id'],
                    'likes': photo['likes']['count'],
                    'comments': photo['comments']['count']
                }
            )
            if num == 2:
                break

        return result

    def user_serch(
            self,
            city_id: int,
            age_from: int,
            age_to: int,
            sex: int,
            relation: int,
            offset=None
    ):
        try:
            profiles = self.ext_api.method(
                'users.search',
                {
                    'city_id': city_id,
                    'age_from': age_from,
                    'age_to': age_to,
                    'sex': sex,
                    'count': 30,
                    'relation': relation,
                    'offset': offset
                }
            )
        except ApiError:
            return

        profiles = profiles['items']
        result = []
        for profile in profiles:
            if profile['is_closed'] is False:
                result.append(
                    {
                        'name': f"{profile['first_name']}\
                              {profile['last_name']}",
                        'id': profile['id']
                    }
                )
        return result
