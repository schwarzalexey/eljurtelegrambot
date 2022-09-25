from telebot import *
import sqlite3
from auth import auth
from info import *

bot = TeleBot('5739731982:AAGctJkddQ3ua_b9LmnCuW7H2vP9IEdSMsA')
conn = sqlite3.connect('db.db3', check_same_thread=False)
cursor = conn.cursor()


def pushDB(uid: int, username: str, subdomain: str, login: str, password: str):
    cursor.execute(
                   'INSERT INTO db (user_id, username, subdomain, login, password) VALUES (?, ?, ?, ?, ?)',
                   (uid, username, subdomain, login, password)
                   )
    conn.commit()


def Markup_MainMenu(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Получить информацию о себе', callback_data='getinfo_'+str(user_id)))
    markup.add(types.InlineKeyboardButton('Получить расписание на неделю', callback_data='getjournal_'+str(user_id)))
    return markup


@bot.message_handler(commands=['start'])
@bot.callback_query_handler(func=lambda call: call.data == "go_back")
def startMsg(msg):
    global chat_id
    global user_id
    if type(msg) == types.CallbackQuery:
        chat_id = msg.message.chat.id
        user_id = msg.message.json['chat']['id']
    else:
        chat_id = msg.chat.id
        user_id = msg.from_user.id
    if not cursor.execute(f"SELECT user_id FROM db WHERE user_id='{user_id}'").fetchone():
        msg = bot.send_message(
                                chat_id,
                                "Для работы с eljur требуется авторизация и домен школы (arh-licey для arh-licey.eljur.ru)\n ",
                                "Введите субдомен:"
        )
        bot.register_next_step_handler(msg, getSub)
    else:
        subdomain = cursor.execute(f"SELECT subdomain FROM db WHERE user_id='{user_id}'").fetchone()[0]
        login = cursor.execute(f"SELECT login FROM db WHERE user_id='{user_id}'").fetchone()[0]
        password = cursor.execute(f"SELECT password FROM db WHERE user_id='{user_id}'").fetchone()[0]
        info = getInfo(subdomain, auth(subdomain, {'username': login, 'password': password})['session'])
        surname, name = info['Фамилия'], info['Имя']
        text = f"Приветствую, {surname} {name}."
        if type(msg) != types.CallbackQuery:
            bot.send_message(chat_id, text, reply_markup=Markup_MainMenu(user_id))
        else:
            message_id, chat_id = msg.message.json['message_id'], msg.message.chat.id
            bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=Markup_MainMenu(user_id))


@bot.callback_query_handler(func=lambda call: call.data[:7] == 'getinfo')
def getInfo_Main(call):
    message_id, chat_id = call.message.json['message_id'], call.message.chat.id
    subdomain_ = cursor.execute(f"SELECT subdomain FROM db WHERE user_id='{call.data.split('_')[1]}'").fetchone()[0]
    login_ = cursor.execute(f"SELECT login FROM db WHERE user_id='{call.data.split('_')[1]}'").fetchone()[0]
    password = cursor.execute(f"SELECT password FROM db WHERE user_id='{call.data.split('_')[1]}'").fetchone()[0]
    info = getInfo(subdomain_, auth(subdomain_, {'username': login_, 'password': password})['session'])
    text = ';\n'.join(f"{x}: {y}" for x, y in info.items())
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Вернуться назад', callback_data="go_back"))
    bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data[:10] == 'getjournal')
def getJournal_Main(call):
    message_id, chat_id = call.message.json['message_id'], call.message.chat.id
    subdomain_ = cursor.execute(f"SELECT subdomain FROM db WHERE user_id='{call.data.split('_')[1]}'").fetchone()[0]
    login_ = cursor.execute(f"SELECT login FROM db WHERE user_id='{call.data.split('_')[1]}'").fetchone()[0]
    password = cursor.execute(f"SELECT password FROM db WHERE user_id='{call.data.split('_')[1]}'").fetchone()[0]
    journal = getJournal(subdomain_, auth(subdomain_, {'username': login_, 'password': password})['session'])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Вернуться назад', callback_data="go_back"))
    text = ''
    for day, lessons in journal.items():
        text += f"{day}, {lessons['date']}:\n"
        for num, lesson in lessons['lessons'].items():
            text += f"└── {num if num != '' else 'Внеурочная деятельность'}. {lesson['name']} 🏠: {str(lesson['hometask']).replace('None', 'Нет')} ✔: {str(lesson['mark'] if lesson['mark'] != '' else 'Н').replace('None', 'Нет')}\n"
        text += '\n'
    bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)



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
    authResult = auth(subdomain.text,
                {
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


#todo: ген картинок расписания + расписание по дням и предыдущим/след неделям
#todo: ф-ия на оценки за четверть/итоговые/посещаемость (если не ебнусь, желательно картинки для вего этого)
#todo: смена пароля в боте при 400 при авторицауии из бд (делогин)

