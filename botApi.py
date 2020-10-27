import random
import requests
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from pivoParser import parsePyaterochka, parseMagnit, parseKb
from pivoParserSelenium import *


def uploadImages(images, offset, vk_session):
    session = requests.Session()
    attachments = []
    i = 0
    upload = vk_api.VkUpload(vk_session)
    while i < 10 and i + offset < len(images):
        image_url = images[i + offset]
        image = session.get(image_url, stream=True)
        photo = upload.photo_messages(photos=image.raw)[0]
        attachments.append(
            'photo{}_{}_{}'.format(photo['owner_id'], photo['id'], photo['access_key'])
        )
        i += 1
    return attachments


def getName(id):
    payload = {'user_id': id, 'access_token': token, 'v': '5.124'}
    response = requests.get("https://api.vk.com/method/users.get", params=payload)

    resp_keys = response.text.split(":")
    print(resp_keys)
    first_name = resp_keys[3]
    first_name = first_name.split(",")[0]
    first_name = first_name[1:]
    first_name = first_name[:-1]
    last_name = resp_keys[4]
    last_name = last_name.split(",")[0]
    last_name = last_name[1:]
    last_name = last_name[:-1]
    print(first_name)
    print(last_name)
    return first_name + " " + last_name


def getAll(chat_id):
    message = "Призываю вас:\n"
    ids = []
    for array in chats[chat_id].poll.values():
        if array is not None:
            for id in array:
                ids.append(id)
    ids=set(ids)
    for id in ids:
        message += getLink(id)
    return message


def getLink(id):
    id = str(id)
    return "[id" + id + "|" + getName(id) + "] \n"


def getPivniye(chat_id):
    ids = "\n"
    print(chats[chat_id].poll.values())
    ids_set = set()
    for element in chats[chat_id].poll.values():
        if element is not None:
            ids_set.update(set(element))
    print(ids_set)
    for id in ids_set:
        ids += getName(id)
    return ids


def getPollInfo(chat_id):
    info = "Инфо по голосам: \n"
    if len(chats[chat_id].poll.keys()) == 0:
        return "никто еще не голосовал"
    for time in chats[chat_id].poll.keys():
        if chats[chat_id].poll.get(time) is not None:
            info += time + ": \n"
            for id in chats[chat_id].poll.get(time):
                info += getName(id) + '\n'
            info += "\n"
    return info


def whoIs(message, members):
    index = random.randrange(0, len(members) - 1)
    while members[index]["member_id"] < 0:
        index = random.randrange(0, len(members) - 1)
    return "Очевидно что " + message + " " + getName(members[index]["member_id"])


def addPollValue(value, id):
    ids = []
    if value in chats[chat_id].poll.keys():
        ids = chats[chat_id].poll.get(value)
        if ids == None:
            ids = []
        if id in ids:
            return
    ids.append(id)
    chats[chat_id].poll.update({value: ids})


def createPollMessage(time_from, time_to, chat_id):
    i = time_from
    poll_data = "Варианты времени:\n"
    time_data = ""
    time_values = []
    while i <= time_to:
        if int(i) != i:
            time_data = str(int(i)) + ":30"
        else:
            time_data = str(int(i)) + ":00"
        time_values.append(time_data)
        poll_data += time_data + "\n"
        i += 0.5
    time_values.append("Не важно")
    chats[chat_id].poll = {key: None for key in time_values}
    print(chats[chat_id].poll)
    return poll_data


def getVoteKeyboard(chat_id):
    settings = dict(one_time=False, inline=True)
    keyboard = VkKeyboard(**settings)
    print(chats[chat_id].poll.keys())
    i = 0
    for time_value in chats[chat_id].poll.keys():
        i += 1
        print("time value" + str(time_value))
        keyboard.add_callback_button(label=time_value, color=VkKeyboardColor.SECONDARY,
                                     payload={"type": "message_new", "text": "я за " + time_value})
        if i % 3 == 0:
            keyboard.add_line()
    keyboard.add_callback_button(label='голоса инфо', color=VkKeyboardColor.SECONDARY)
    keyboard.add_callback_button(label='кто идет', color=VkKeyboardColor.SECONDARY)

    return keyboard


# API-ключ созданный ранее
token = "5053247a0cad934c798750243f5425b84ae062a99be994dce2194b7255b8d2afa066a91769e352f2a8f8c"
# Авторизуемся как сообщество
vk_session = vk_api.VkApi(token=token, api_version='5.124')
group_id = "199735512"
# Работа с сообщениями
longpoll = VkBotLongPoll(vk_session, group_id)
vk = vk_session.get_api()


class Chat:
    def __init__(self):
        self.poll_created = 0
        self.poll = {}
        pass


chats = {}


def showPoll():
    if not chats[chat_id].poll_created:
        vk.messages.send(
            random_id=random_id,
            chat_id=chat_id,
            message="Нет опроса")
        # continue
    else:
        vk.messages.send(
            random_id=random_id,
            chat_id=chat_id,
            message="Текущий опрос",
            keyboard=keyboard.get_keyboard()
        )


def showVoteInfoInDetails():
    message: str
    if not chats[chat_id].poll_created:
        message = "Нет опроса"
    else:
        message = getPollInfo(chat_id)
    vk.messages.send(
        random_id=random_id,
        chat_id=chat_id,
        message=message,
    )


def getPivoDrinkers():
    message = "Идут пить пиво :" + getPivniye(chat_id)
    vk.messages.send(
        random_id=random_id,
        chat_id=chat_id,
        message=message,
    )


def handleVote():
    if not chats[chat_id].poll_created:
        message = "Нет опроса"
    else:
        time = "empty"
        try:
            time = str(event.message.text[33:])
            print(time)
            if time not in chats[chat_id].poll.keys():
                message = "Время не в диапазоне соси"
            else:
                addPollValue(time, event.message.from_id)
                message = "Принял"
        except BaseException:
            message = "Неверно задано время"
    print(chats[chat_id].poll)
    vk.messages.send(
        random_id=random_id,
        chat_id=chat_id,
        message=message,
    )


# Основной цикл
# FIXME [ZK]: пивобот does not follows exact order of commands
for event in longpoll.listen():
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and ("@public" + group_id) in str(event):
            if str(event.message.text[33:]) in chats[chat_id].poll.keys():
                handleVote()
                continue
            if "голоса инфо" in str(event):
                showVoteInfoInDetails()
                continue
            if "кто идет" in str(event):
                getPivoDrinkers()
                continue

        if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat and (
                "пивобот " in str(event) or "Пивобот " in str(event)):
            random_id = random.randrange(10000, 90000)
            chat_id = int(event.chat_id)
            if chat_id not in chats.keys():
                chat = Chat()
                chats.update({chat_id: chat})
            print(event.message)
            print(chats.values())
            keyboard = getVoteKeyboard(chat_id)
            if "опрос показать" in str(event):
                showPoll()
                continue
            if "пиво попито" in str(event):
                chats[chat_id].poll_created = 0
                chats[chat_id].poll = {}
                vk.messages.send(
                    random_id=random_id,
                    chat_id=chat_id,
                    message="Везет)",
                )
            if "общий сбор" in str(event):
                vk.messages.send(
                    random_id=random_id,
                    chat_id=chat_id,
                    message=getAll(chat_id),
                )

            if "кто идет" in str(event):
                getPivoDrinkers()
                continue
            if "кто" in str(event):
                members = \
                    vk.messages.getConversationMembers(peer_id=2000000000 + event.chat_id, v=5.124, group_id=group_id)[
                        "items"]
                message = whoIs(event.message.text[11:], members)
                vk.messages.send(
                    random_id=random_id,
                    chat_id=chat_id,
                    message=message,
                )
            if 'опрос время' in str(event):
                time = "empty"
                try:
                    times = str(event.message.text).split("опрос время ")[1]
                    times = times.split(" ")
                    print(times)
                    if int(times[0]) > int(times[1]) or int(times[1]) - int(times[0]) > 4:
                        vk.messages.send(
                            random_id=random_id,
                            chat_id=chat_id,
                            message="Ты че дурак чтоли а",
                        )
                        continue
                    poll_message = createPollMessage(int(times[0]), int(times[1]), chat_id)
                    chats[chat_id].poll_created = 1
                    keyboard = getVoteKeyboard(chat_id)
                    showPoll()
                    continue
                except BaseException:
                    vk.messages.send(
                        random_id=random_id,
                        chat_id=chat_id,
                        message="Неверно задано время",
                    )

            if "голоса инфо" in str(event):
                showVoteInfoInDetails()
                continue
            if "лучшее пиво" in str(event):
                vk.messages.send(
                    random_id=random_id,
                    chat_id=chat_id,
                    message="Конечно же ипа",
                )
            if "команды" in str(event):
                message = """Команды бота: \n
                          пивобот кто идет - посмотреть кто готов идти пить пиво \n
                          пивобот опрос время #время_от #время_до - опрос по времени в интервале, разница не более 4 часов\n 
                          пивобот опрос показать - выводит опрос\n
                          пивобот скидкаонлайн #[пятерочка/магнит/кб] - акции магазина со skidkaonline\n
                          пивобот едадил #[пятерочка/магнит/кб] - акции магазина с едадила\n
                          пивобот голоса инфо - показать результаты опроса по времени\n
                          пивобот лучшее пиво - показать лучшее пиво во вселенной\n
                          пивобот кто #текст - ну вы поняли\n"""

                vk.messages.send(
                    random_id=random_id,
                    chat_id=chat_id,
                    message=message,
                )
            if "едадил" in str(event):
                message = ''
                if "пятерочка" in str(event):
                    products = edadeal_parser("5ka")
                    message = "Скидки в пятерочке: \n"
                elif "магнит" in str(event):
                    products = edadeal_parser("magnit-univer")
                    message = "Скидки в магните: \n "
                elif "кб" in str(event):
                    products = edadeal_parser("krasnoeibeloe")
                    message = "Скидки в кб: \n"
                else:
                    vk.messages.send(
                        random_id=random_id,
                        chat_id=chat_id,
                        message="Не знаю такого магазина",
                    )
                    continue
                for product in products:
                    message += product['description'] + " \n " + product['priceNew'] + "\n "
                vk.messages.send(
                    random_id=random_id,
                    chat_id=chat_id,
                    message=message,
                )

            if "скидкаонлайн" in str(event):
                message = ''
                if "пятерочка" in str(event):
                    images = parsePyaterochka()
                    message = "Скидки в пятерочке"
                elif "магнит" in str(event):
                    images = parseMagnit()
                    message = "Скидки в магните "
                elif "кб" in str(event):
                    products = parseKb()
                    message = "Скидки в кб: \n"
                    for product in products.keys():
                        message += product + " : " + products[product] + "р \n"
                    vk.messages.send(
                        random_id=random_id,
                        chat_id=chat_id,
                        message=message,
                    )
                    continue
                else:
                    vk.messages.send(
                        random_id=random_id + i,
                        chat_id=chat_id,
                        message="Я не знаю такого магазина",
                    )
                    continue
                length = len(images)
                i = 0
                while True:
                    attachments = uploadImages(images, i, vk)
                    vk.messages.send(
                        random_id=random_id + i,
                        chat_id=chat_id,
                        message=message,
                        attachment=','.join(attachments)
                    )
                    i += 10
                    if i > length:
                        break
