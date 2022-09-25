from telebot import *
import sqlite3
from auth import auth
from info import *
from draw import *
from datetime import date, timedelta

bot = TeleBot('5739731982:AAGctJkddQ3ua_b9LmnCuW7H2vP9IEdSMsA')
conn = sqlite3.connect('db.db3', check_same_thread=False)
cursor = conn.cursor()


def pushDB(uid: int, username: str, subdomain: str, login: str, password: str):
    cursor.execute(
                   'INSERT INTO db (user_id, username, subdomain, login, password) VALUES (?, ?, ?, ?, ?)',
                   (uid, username, subdomain, login, password)
                   )
    conn.commit()


def markupMainMenu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Получить информацию о себе', callback_data='getinfo'))
    markup.add(types.InlineKeyboardButton('Получить расписание на неделю', callback_data='getjournal_0'))
    return markup


def getMainData(user_id):
    return [
        cursor.execute(f"SELECT subdomain FROM db WHERE user_id='{user_id}'").fetchone()[0],
        cursor.execute(f"SELECT login FROM db WHERE user_id='{user_id}'").fetchone()[0],
        cursor.execute(f"SELECT password FROM db WHERE user_id='{user_id}'").fetchone()[0]
    ]


@bot.message_handler(commands=['start'])
@bot.callback_query_handler(func=lambda call: call.data in ("go_back", "go_back_journal"))
def startMsg(msg):
    global chat_id
    global user_id
    if type(msg) == types.CallbackQuery:
        chat_id = msg.message.chat.id
        user_id = msg.message.json['chat']['id']
        data_cb = msg.data
        message_id = msg.message.json['message_id']
        if msg.data == "go_back_journal":
            bot.delete_message(chat_id, message_id)
    else:
        chat_id = msg.chat.id
        user_id = msg.from_user.id
        message_id = msg.id

    if not cursor.execute(f"SELECT user_id FROM db WHERE user_id='{user_id}'").fetchone() :
        msg = bot.send_message(
                                chat_id,
                                "Для работы с eljur требуется авторизация и домен школы (arh-licey для arh-licey.eljur.ru)\n "
                                "Введите субдомен:"
        )
        bot.register_next_step_handler(msg, getSub)
    else:
        data = getMainData(user_id)
        info = getInfo(data[0], auth(data[0], {'username': data[1], 'password': data[2]})['session'])
        surname, name = info['Фамилия'], info['Имя']
        text = f"Приветствую, {surname} {name}."
        if type(msg) == types.CallbackQuery and msg.data != "go_back_journal":
            bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markupMainMenu())
        else:
            bot.send_message(chat_id, text, reply_markup=markupMainMenu())


@bot.callback_query_handler(func=lambda call: call.data == 'getinfo')
def getInfo_Main(call):
    message_id = call.message.json['message_id']
    chat_id = call.message.chat.id
    data = getMainData(call.message.json['chat']['id'])
    info = getInfo(data[0], auth(data[0], {'username': data[1], 'password': data[2]})['session'])
    text = ';\n'.join(f"{x}: {y}" for x, y in info.items())
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Вернуться назад', callback_data="go_back"))
    bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data[:11] == 'getjournal_')
def getJournal_Main(call):
    message_id = call.message.json['message_id']
    chat_id = call.message.chat.id
    week = int(call.data.split('_')[1])
    if call.data[-1] == 'j':
        bot.delete_message(chat_id, call.message.json['message_id'])
    datetoday = date.today() + timedelta(days=7 * week)
    start_date = datetoday - timedelta(datetoday.weekday())
    end_date = start_date + timedelta(days=6)
    markup = types.InlineKeyboardMarkup(row_width=8)
    markup.add(types.InlineKeyboardButton('← Предыдущая неделя', callback_data=f"getjournal_{week - 1}"))
    markup.add(types.InlineKeyboardButton('Понедельник, ' + str(start_date), callback_data=f"getjournalday_1_{week}"))
    markup.add(types.InlineKeyboardButton('Вторник, ' + str(start_date + timedelta(days=1)), callback_data=f"getjournalday_2_{week}"))
    markup.add(types.InlineKeyboardButton('Среда, ' + str(start_date + timedelta(days=2)), callback_data=f"getjournalday_3_{week}"))
    markup.add(types.InlineKeyboardButton('Четверг, ' + str(start_date + timedelta(days=3)), callback_data=f"getjournalday_4_{week}"))
    markup.add(types.InlineKeyboardButton('Пятница, ' + str(start_date + timedelta(days=4)), callback_data=f"getjournalday_5_{week}"))
    markup.add(types.InlineKeyboardButton('Суббота, ' + str(start_date + timedelta(days=5)), callback_data=f"getjournalday_6_{week}"))
    markup.add(types.InlineKeyboardButton('Следующая неделя →', callback_data=f"getjournal_{week + 1}"))
    markup.add(types.InlineKeyboardButton('Вернуться назад', callback_data="go_back"))
    if call.data[-1] != 'j':
        bot.edit_message_text(f"Текущая неделя - c {start_date} по {end_date}.\n Выберите день или переключите неделю", chat_id=chat_id, message_id=message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, f"Текущая неделя - c {start_date} по {end_date}.\n Выберите день или переключите неделю", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data[:14] == 'getjournalday_')
def getJournal_day(call):
    chat_id = call.message.chat.id
    user_id = call.message.json["chat"]["id"]
    data = getMainData(user_id)
    journal = getJournal(data[0], auth(data[0], {'username': data[1], 'password': data[2]})['session'], week=int(call.data.split('_')[2]))
    draw(journal[call.data.split('_')[1]], user_id)
    bot.delete_message(chat_id, call.message.json['message_id'])
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton('Выбрать другой день', callback_data="getjournal_0_j"))
    markup.add(types.InlineKeyboardButton('Вернуться назад', callback_data="go_back_journal"))
    bot.send_photo(chat_id, types.InputFile(f'C:\\Users\\retys\\PycharmProjects\\pythonProject1\\day_{user_id}.jpg'), reply_markup=markup)

def getSub(msg):
    global subdomain
    subdomain = msg
    msg = bot.send_message(chat_id, "Введите логин:")
    bot.register_next_step_handler(msg, getLog)


def getLog(msg):
    global login
    login = msg
    msg = bot.send_message(msg.chat.id, "Введите пароль:")
    bot.register_next_step_handler(msg, authFinal)


def authFinal(msg):
    authResult = auth(subdomain.text, {
                    'username': login.text,
                    'password': msg.text
                })
    if not authResult['result']:
        bot.send_message(msg.chat.id, authResult['error_msg'] + '\n Пройдите авторизацию ещё раз.')
    else:
        pushDB(
               msg.from_user.id,
               msg.from_user.username,
               subdomain.text,
               login.text,
               msg.text,
               )

        bot.send_message(msg.chat.id, "Авторизация прошла удачно.")
    startMsg(msg)


bot.polling(none_stop=True)


# todo: расписание по дням и предыдущим/след неделям
# todo: ф-ия на оценки за четверть/итоговые/посещаемость (если не ебнусь, желательно картинки для вего этого)
# todo: смена пароля в боте при 400 при авторицауии из бд (делогин)
