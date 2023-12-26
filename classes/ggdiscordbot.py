from classes.bunitime import BuniTime
from datetime import datetime, timezone
from discordwebhook import Discord
from bs4 import BeautifulSoup
import requests
import time
import openai
from googleapiclient.discovery import build
import json


class PentaBot:
    def __init__(self):
        self.discord = Discord(url=WEBHOOK_URL)
        self.streamer_nickname = STREAMER_NAME
        self.goodgame_base_url = GOODGAME_BASE_URL
        self.goodgame_stream_url = GOODGAME_BASE_URL + "/" + self.streamer_nickname
        self.youtube_channel_id = YOUTUBE_CHANNEL_ID
        self.youtube_api_key = YOUTUBE_API_KEY
        self.is_streamer_online_now = False
        self.is_notify_sent = False
        self.openai_key = OPENAI_KEY
        self.stream_ending_time = datetime.now(timezone.utc)
        self.bunitime = BuniTime()
        self.is_buni_sent = False

    def run(self):
        # В бесконечном цике
        while True:
            # Пробуем дернуть гудгейм урл и получить жсон с инфой
            try:
                stream_info_json = self.get_stream_info_json()
            # Если не получилось, хуй с ним, попробуем позже
            except:
                pass
            # Если получилось
            else:
                # Смотрим, онлайн ли стримлен
                try:
                    is_stream_online = self.check_gg_streamer_online(stream_info_json)
                # Если чот пошло не так, то наверное, он не онлайн
                except:
                    is_stream_online = False
                # Если он онлайн и мы еще не слали уведомления в Дискорд, то
                if is_stream_online and not self.is_notify_sent:
                    # Сбросим буни
                    self.is_buni_sent = False
                    # Задаем на уровне класса переменную, чтобы запомнить, что он онлайн
                    self.is_streamer_online_now = True
                    # Получем описание стрима и название игры
                    title_playing = self.get_title_playing(stream_info_json)
                    game_playing = self.get_game_playing(stream_info_json)

                    # Получаем анонс от чатгпт, если не получилось, хуй с ней, будет пустая
                    joke_text = ""
                    try:
                        joke_text = self.get_joke(game_playing, title_playing)
                    except:
                        pass

                    # Получаем ссылку на ютуб-трансляцию и генерим текст с ней, если не получилось, хуй с ней, не будет ее
                    youtube_text = ""
                    try:
                        youtube_url = self.get_live_stream_url(self.youtube_channel_id)
                        if len(youtube_url) > 0:
                            youtube_text = "Лайкосики на ютуб не забываем выгружать!\n{}".format(youtube_url)
                        else:
                            youtube_text = "Ссылочку на ютуб найдите сами, у меня не получилося =("
                    except:
                        youtube_text = "Ссылочку на ютуб найдите сами, у меня не получилося =("

                    # Получаем картинку от чатгпт, если не получилось, хуй с ней, не будет ее
                    pic_url = ""
                    try:
                        pic_url = self.get_pic(game_playing, title_playing)
                    except:
                        pass

                    # Генерим болванчик для анонса
                    announcing_text = "@everyone, {} стартовал стрим!\n\n{}\n\n{}\n\n".format(self.streamer_nickname, youtube_text, joke_text.strip())

                    # Если нет пикчи, то отправляем кривой пик Пемзы
                    if len(pic_url) == 0:
                        pic_url = "https://goodgame.ru/files/pics/172232_P8x7.jpg"

                    self.discord.post(
                        content=announcing_text,
                        embeds=[
                            {
                                "author": {
                                "name": self.goodgame_stream_url,
                                "url": self.goodgame_stream_url
                                },
                                "title": game_playing,
                                "image": {"url": pic_url}
                             }
                        ]
                    )

                    self.is_notify_sent = True
                # Когда нет стрима
                if not is_stream_online:
                    # Значит был онлайн, записываем время выхода
                    if self.is_streamer_online_now:
                        self.stream_ending_time = datetime.now(timezone.utc)
                    # И резетаем переменные
                    self.is_streamer_online_now = False
                    self.is_notify_sent = False
                    # Чекаем, не надо ли забунить
                    need_to_buni = self.bunitime.is_it_time_to_buni(self.stream_ending_time)
                    # Если надо, буним
                    if need_to_buni and not self.is_buni_sent:
                        # Буним
                        self.discord.post(content="<:U_:696468234102112337>")
                        # Булим
                        try:
                            booleng = self.get_booleng(self.streamer_nickname)
                            self.discord.post(content=booleng)
                        except:
                            pass
                        # Отмечаем, что побунили
                        self.is_buni_sent = True
                    # Сбрасываем буни при наступлении нового дня, если даже уже бунили
                    if self.is_buni_sent:
                        last_stream_day = self.stream_ending_time.strftime("%d")
                        real_day = datetime.now(timezone.utc).strftime("%d")
                        if last_stream_day != real_day:
                            self.is_buni_sent = False
                            self.stream_ending_time = datetime.now(timezone.utc)



            # Спим три минуты
            time.sleep(180)

    # Получаем хтмл со страницы ГГ и отдаем жсон с инфой
    def get_stream_info_json(self):
        r = requests.get(self.goodgame_stream_url).text
        html_content = BeautifulSoup(r, 'lxml')
        entire = html_content.find('div', id='entire')
        script = entire.find('script')
        json_var_str = str(script)
        channel = json_var_str.split('channel:')[1]
        raw_json = channel.split("\n")[0]
        info = json.loads(raw_json)
        return info

    # Получаем из жсона инфо, играет ли пемза
    def check_gg_streamer_online(self, info_json):
        is_online = info_json['online']
        if is_online == 1:
            return True
        else:
            return False

    # Получаем из жсона инфо, во что играет пемза
    def get_game_playing(self, info_json):
        game = info_json['game']
        if len(game) == 0:
            return "х пойми что"
        else:
            return game

    # Получаем из жсона инфо, как озаглавил пемза стрим
    def get_title_playing(self, info_json):
        game = info_json['title']
        if len(game) == 0:
            return "х пойми что"
        else:
            return game

    # Получаем шутейку из чатгпт
    def get_joke(self, game, title):
        openai.api_key = self.openai_key
        model_engine = "text-davinci-003"
        text = ""
        while (len(text) == 0) or ("войн" in text):
            prompt = "Придумай смешной текст анонса стрима игры {} с описанием {}".format(game, title)

            max_tokens = 128

            completion = openai.Completion.create(
                engine=model_engine,
                prompt=prompt,
                max_tokens=1024,
                temperature=0.5,
                top_p=1,
                frequency_penalty=0,
                 presence_penalty=0
            )

            text = completion.choices[0].text
        return text

    # Получаем буленг
    def get_booleng(self, nickname):
        openai.api_key = self.openai_key
        model_engine = "text-davinci-003"
        text = ""
        while (len(text) == 0) or ("войн" in text):
            prompt = "Придумай текст, частушку или четверостишие, на твой выбор, о том, что стример {} долго не запускал стрим.".format(nickname)

            max_tokens = 128

            completion = openai.Completion.create(
                engine=model_engine,
                prompt=prompt,
                max_tokens=1024,
                temperature=0.5,
                top_p=1,
                frequency_penalty=0,
                 presence_penalty=0
            )

            text = completion.choices[0].text
        return text

    # Получаем картинку из чатгпт
    def get_pic(self, game, title):
        openai.api_key = self.openai_key
        response = openai.Image.create(
            prompt="Picture please {} game".format(game),
            n=1,
            size="512x512",
        )
        return response["data"][0]["url"]

    # Получаем ссылку на ютуб трансляцию
    def get_live_stream_url(self, channel_id):
        api_key = self.youtube_api_key
        # Создаем объект YouTube API
        youtube = build('youtube', 'v3', developerKey=api_key)
        # Получаем информацию о текущей трансляции канала
        live_streams = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            type='video',
            eventType='live'
        ).execute()
        # Если есть активная трансляция, возвращаем ссылку
        if live_streams['items']:
            video_id = live_streams['items'][0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"
        # Если нет активной трансляции, возвращаем сообщение
        return ""


if __name__ == '__main__':
    PentaBot().run()
