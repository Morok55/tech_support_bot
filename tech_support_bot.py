import telebot
from telebot import types
import sqlite3
import datetime
import collections
import random
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(TOKEN)

players = {}    # обращения пользователей (key = count(уникальный код)) (count: [id, today, style, question])
answers = {}    # ответы администрации (key = count(уникальный код)) (count: answer)
faq = {}    # часто задаваемые вопросы (key = count_faq(уникальный код)) (count_faq: [problem, response])
admins = [1135036918]   # telegram id админов

try:
    conn = sqlite3.connect('tech_support_database.sql')
    cur = conn.cursor()

    cur.execute('SELECT count, id, today, style, question, answer FROM users')
    people = cur.fetchall()

    cur.execute('SELECT count_faq, problem, response FROM FAQ')
    qq = cur.fetchall()

    cur.close()
    conn.close()

    for i in people:
        players[i[0]] = [i[1], i[2], i[3], i[4]]
        if i[5]:
            answers[i[0]] = i[5]

    for m in qq:
        if m[1] and m[2]:
            faq[m[0]] = [m[1], m[2]]


except sqlite3.OperationalError:
    pass

print('Players:', players)
print('\nAnswers:', answers)
print('\nFAQ:', faq)


if players:
    [count] = collections.deque(players, maxlen=1)
else:
    count = 0

if not faq:
    count_faq = 1


print('\nCount =', count)

def main_menu(user):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton('Мои обращения')
    btn2 = types.KeyboardButton('Написать обращение')
    btn3 = types.KeyboardButton('Часто задаваемые вопросы')
    markup.row(btn1, btn2)
    markup.row(btn3)

    bot.send_message(user, '📁 Выберите пункт меню', reply_markup=markup)

def admin_menu(user):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    btn1 = types.KeyboardButton('Ответить на обращения')
    btn2 = types.KeyboardButton('⁉️ Часто задаваемые вопросы')

    markup.add(btn1, btn2)

    bot.send_message(user, 'Добро пожаловать в админ панель, чтобы выйти из неё пропишите команду /start',
                     reply_markup=markup)


def see_appeals(user):
    my_appeal = []
    for key, value in players.items():
        if value[0] == user:
            my_appeal.append(key)

    markup = types.InlineKeyboardMarkup()

    btns = []

    info = ''
    for num, key in enumerate(my_appeal):
        call_back = '|'.join(['my_appeals', str(key)])
        info += f'Обращение № {num + 1}\n{players[key][2].capitalize()}: {players[key][3][:29]} ...\n\n'

        btns.append(types.InlineKeyboardButton(f'{num + 1}', callback_data=call_back))

    markup.add(*btns)

    if info:
        bot.send_message(user, f'{info}Нажмите на кнопку с номером обращения, которое хотите посмотреть',
                         reply_markup=markup)
    else:
        bot.send_message(user, 'Вы не оставляли обращения')

def list_faq_admin(user):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton('Добавить', callback_data='add_faq')
    markup.add(btn1)

    if faq:
        btn2 = types.InlineKeyboardButton('Удалить', callback_data='delete_faq')
        markup.add(btn2)

        info_faq = ''

        for x, quest in enumerate(faq.values()):
            info_faq += f'\n\n№ {x + 1}: {quest[0]}'

        bot.send_message(user, f'Список FAQ:{info_faq}', reply_markup=markup)

    else:
        bot.send_message(user, 'Список FAQ:\n\nСписок пуст, нажмите "Добавить", чтобы добавить вопрос',
                         reply_markup=markup)

def list_faq_user(user):
    markup = types.InlineKeyboardMarkup(row_width=2)

    if faq:
        info_faq = ''

        btns_faq = []

        for i, quest in enumerate(faq.items()):
            see_faq = '|'.join(['see_faq', str(quest[0])])
            info_faq += f'\n\n№ {i + 1}: {quest[1][0]}'
            btns_faq.append(types.InlineKeyboardButton(f'{i + 1}', callback_data=see_faq))

        markup.add(*btns_faq)

        bot.send_message(user, f'Список FAQ:{info_faq}\n\nНажмите на кнопку с номером вопроса, который хотите посмотреть', reply_markup=markup)

    else:
        bot.send_message(user, 'Список FAQ:\n\nСписок пока что пуст',
                         reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user.id

    conn = sqlite3.connect('tech_support_database.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (count int, id int, today varchar, style varchar, question varchar, answer varchar)')

    cur.execute('CREATE TABLE IF NOT EXISTS FAQ (count_faq int, problem varchar, response varchar)')

    conn.commit()

    cur.close()
    conn.close()

    main_menu(user)

@bot.message_handler(commands=['admin'])
def admin(message):
    user = message.from_user.id
    if user in admins:
        admin_menu(user)


@bot.message_handler(content_types=['text'])
def functions(message):
    user = message.from_user.id
    text = message.text

    if text == 'Мои обращения':
        see_appeals(user)


    elif text == 'Написать обращение':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        btn1 = types.KeyboardButton('Жалоба')
        btn2 = types.KeyboardButton('Вопрос')
        btn3 = types.KeyboardButton('❌ Отмена')
        markup.row(btn1, btn2)
        markup.row(btn3)

        bot.send_message(user, 'Укажите тип обращения', reply_markup=markup)

        bot.register_next_step_handler(message, question)

    elif text == 'Часто задаваемые вопросы':
        list_faq_user(user)

    elif text == '❌ Отмена':
        main_menu(user)

    elif text == 'Ответить на обращения' and user in admins:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        btn1 = types.KeyboardButton('Любое')
        btn2 = types.KeyboardButton('По номеру')
        btn3 = types.KeyboardButton('Отмена')
        markup.row(btn1, btn2)
        markup.row(btn3)

        bot.send_message(user, 'Как вы хотите выбрать обращение для ответа?', reply_markup=markup)

        bot.register_next_step_handler(message, choice_answer)

    elif text == '⁉️ Часто задаваемые вопросы' and user in admins:
        list_faq_admin(user)

    elif text == 'Отмена':
        admin_menu(user)

def choice_answer(message):
    user = message.from_user.id
    text = message.text

    no_answer = []

    for key in players.keys():
        if key not in answers.keys():
            no_answer.append(key)

    if not no_answer:
        bot.send_message(user, 'В данный момент нет активных обращений')
    else:
        if text == 'Любое':
            number = random.choice(no_answer)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn3 = types.KeyboardButton('Отмена')
            markup.add(btn3)
            bot.send_message(user, f'Ваш номер вопроса - {number}', reply_markup=markup)

            answer(message, number, no_answer)

        elif text == 'По номеру':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn3 = types.KeyboardButton('Отмена')
            markup.add(btn3)

            bot.send_message(user, 'Введите номер вопроса', reply_markup=markup)

            bot.register_next_step_handler(message, answer, 0, no_answer)


    if text == 'Отмена':
        admin_menu(user)


def answer(message, number, no_answer):
    user = message.from_user.id
    text = message.text

    try:
        if number == 0:
            number = int(text)

        if text == 'Отмена':
            admin_menu(user)

        else:
            if number in no_answer:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                btn3 = types.KeyboardButton('Отмена')
                markup.add(btn3)

                bot.send_message(user, f'📅 Дата обращения - {players[number][1]}\n\n 🔲 Тип: <b>{players[number][2].capitalize()}</b>\n 🔲 Содержание: \n<i>{players[number][3]}</i>', parse_mode='html')
                bot.send_message(user, 'Дайте ответ на это обращение', reply_markup=markup)

                bot.register_next_step_handler(message, right_answer, number)
            else:
                bot.send_message(user, 'Ошибка! Данного обращения нет или на него уже ответили. Введите другой номер вопроса')
                bot.register_next_step_handler(message, answer, 0, no_answer)


    except ValueError:
        if text == 'Отмена':
            admin_menu(user)
        else:
            bot.send_message(user, 'Ошибка! Введите целое число')

            bot.register_next_step_handler(message, answer, 0, no_answer)


def right_answer(message, number):
    user = message.from_user.id
    text = message.text

    if text == 'Отмена':
        admin_menu(user)

    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton('Да')
        btn2 = types.KeyboardButton('Нет')
        markup.add(btn1, btn2)

        bot.send_message(user, f'Ваш ответ:\n{text}\n\nВы действительно хотите отправить данный ответ клиенту?', reply_markup=markup)
        bot.register_next_step_handler(message, set_answer, number, text)

def set_answer(message, number, text_answer):
    user = message.from_user.id
    text = message.text

    if text == 'Да':
        conn = sqlite3.connect('tech_support_database.sql')
        cur = conn.cursor()

        answers[number] = text_answer

        cur.execute("UPDATE users SET answer=(?) WHERE count=(?)", (text_answer, number))
        conn.commit()

        cur.close()
        conn.close()

        bot.send_message(players[number][0], f'<b>Тех. поддержка ответила на ваш вопрос.</b>\n\n📅 Дата обращения - {players[number][1]}\n\n 🔲 Тип: {players[number][2].capitalize()}\n 🔲 Содержание: \n<i>{players[number][3]}</i>\n\n✅ <b>Ответ тех. поддержки:</b> \n<i>{text_answer}</i>', parse_mode='html')

        bot.send_message(user, 'Ваш ответ отправлен клиенту')
        admin_menu(user)

    elif text == 'Нет':
        admin_menu(user)



def question(message):
    user = message.from_user.id
    text = message.text

    if text == 'Жалоба':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn3 = types.KeyboardButton('❌ Отмена')
        markup.add(btn3)

        bot.send_message(user, 'Напишите суть вашей жалобы', reply_markup=markup)

        bot.register_next_step_handler(message, picture, 'жалоба')

    elif text == 'Вопрос':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn3 = types.KeyboardButton('❌ Отмена')
        markup.add(btn3)

        bot.send_message(user, 'Напишите суть вашего вопроса', reply_markup=markup)

        bot.register_next_step_handler(message, picture, 'вопрос')


    elif text == '❌ Отмена':
        main_menu(user)


def picture(message, style):
    user = message.from_user.id
    question_1 = message.text

    if message.text == '❌ Отмена':
        main_menu(user)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        btn1 = types.KeyboardButton('Без изображения 🖼️')
        btn3 = types.KeyboardButton('❌ Отмена')
        markup.add(btn1, btn3)

        bot.send_message(user, 'Пришлите изображение (максимум одно)', reply_markup=markup)

        bot.register_next_step_handler(message, get_broadcast_picture, style, question_1)


def last(message, style, question_1, file=None):
    user = message.from_user.id
    text = message.text
    global count
    today = datetime.date.today()
    today = today.strftime("%d-%m-%Y")

    if text == 'Да':
        conn = sqlite3.connect('tech_support_database.sql')
        cur = conn.cursor()
        count += 1
        players[count] = [user, today, style, question_1]

        cur.execute("INSERT INTO users (count, id, today, style, question) VALUES ('%s', '%s', '%s', '%s', '%s')" % (count, user, today, style, question_1))
        conn.commit()

        cur.close()
        conn.close()

        if file:
            for k in admins:
                bot.send_photo(k, file, caption=f'№ {count}\n⚠️В тех поддержку поступила новая жалоба\n\nТип: <b>{style.capitalize()}</b> \nСодержание:\n<i>{question_1}</i>', parse_mode='html')
        else:
            for k in admins:
                bot.send_message(k, f'№ {count}\n⚠️В тех поддержку поступила новая жалоба\n\nТип: <b>{style.capitalize()}</b> \nСодержание:\n<i>{question_1}</i>', parse_mode='html')

        bot.send_message(user, 'Данная жалоба перенаправлена в тех. поддержку. Ждите вам ответят')
        main_menu(user)
        print(players)

    elif text == 'Нет':
        main_menu(user)

def add_answer_faq(message):
    user = message.from_user.id
    text = message.text

    if text == 'Отмена':
        admin_menu(user)
    else:
        bot.send_message(user, 'Напишите ответ на вопрос')

        bot.register_next_step_handler(message, choice_add_faq, text)

def choice_add_faq(message, ques):
    user = message.from_user.id
    text = message.text

    if text == 'Отмена':
        admin_menu(user)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton('Да')
        btn2 = types.KeyboardButton('Нет')
        markup.add(btn1, btn2)

        bot.send_message(user, f'<b>Вопрос:</b> {ques}\n<b>Ответ:</b> \n{text}\n\nВы действительно хотите добавить этот вопрос к списку FAQ?', reply_markup=markup, parse_mode='html')

        bot.register_next_step_handler(message, full_add_faq, ques, text)

def full_add_faq(message, ques, ans):
    user = message.from_user.id
    text = message.text
    global count_faq

    if text == 'Да':
        conn = sqlite3.connect('tech_support_database.sql')
        cur = conn.cursor()

        if faq:
            [count_faq] = collections.deque(faq, maxlen=1)
            count_faq += 1

        faq[count_faq] = [ques, ans]

        cur.execute("INSERT INTO FAQ (count_faq, problem, response) VALUES ('%s', '%s', '%s')" % (count_faq, ques, ans))
        conn.commit()

        cur.close()
        conn.close()

        bot.send_message(user, 'Данный вопрос был добавлен в список FAQ')

        admin_menu(user)

    elif text == 'Нет':
        admin_menu(user)


@bot.message_handler(content_types=['photo'])
def get_broadcast_picture(message, style=None, question_1=None):
    user = message.from_user.id
    text = message.text

    if text == 'Без изображения 🖼️':
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton('Да')
        btn2 = types.KeyboardButton('Нет')
        markup.add(btn1, btn2)

        bot.send_message(user, f'Тип обращения: <b>{style.capitalize()}</b>\nСодержание:\n<i>{question_1}</i>\n\nВы действительно хотите отправить данное обращение на рассмотрение администрации?', reply_markup=markup, parse_mode='html')
        bot.register_next_step_handler(message, last, style, question_1)

    elif text == '❌ Отмена':
        main_menu(user)

    else:
        if style != None and question_1 != None:
            file_path = bot.get_file(message.photo[1].file_id).file_path
            file = bot.download_file(file_path)


            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            btn1 = types.KeyboardButton('Да')
            btn2 = types.KeyboardButton('Нет')
            markup.add(btn1, btn2)

            bot.send_photo(user, file, caption=f'Тип обращения: <b>{style.capitalize()}</b>\nСодержание:\n<i>{question_1}</i>\n\nВы действительно хотите отправить данное обращение на рассмотрение администрации?', reply_markup=markup, parse_mode='html')

            bot.register_next_step_handler(message, last, style, question_1, file)


@bot.callback_query_handler(func=lambda call: True)
def callback_users(call):
    try:
        call_data = call.data.split('|')[0]
        key = int(call.data.split('|')[1])
    except IndexError:
        call_data = call.data
    user = call.from_user.id

    if call_data == 'my_appeals':
        bot.delete_message(user, call.message.message_id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn2 = types.InlineKeyboardButton('⬅️Назад', callback_data='back')

        if key in answers.keys():
            see_answer = '|'.join(['see_answer', str(key)])
            flag_answer = 'Ответ дан ✅'
            btn1 = types.InlineKeyboardButton('Посмотреть ответ', callback_data=see_answer)
            markup.add(btn1)

        else:
            delete_question = '|'.join(['delete_question', str(key)])
            flag_answer = 'Без ответа ❌'
            btn1 = types.InlineKeyboardButton('Удалить обращение', callback_data=delete_question)
            markup.add(btn1)

        markup.add(btn2)

        bot.send_message(user, f'📅 Дата обращения - {players[key][1]}\n\n 🔲 Тип: <b>{players[key][2].capitalize()}</b>\n 🔲 Содержание: \n<i>{players[key][3]}</i> \n\n{flag_answer}', reply_markup=markup, parse_mode='html')

    elif call_data == 'back':
        bot.delete_message(user, call.message.message_id)

        see_appeals(user)

    elif call_data == 'delete_question':
        _ = players.pop(key, None)

        conn = sqlite3.connect('tech_support_database.sql')
        cur = conn.cursor()

        cur.execute("delete from users where count=(?)", (key,))
        conn.commit()

        cur.close()
        conn.close()

        bot.answer_callback_query(call.id, 'Данное обращение удалено')

        bot.delete_message(user, call.message.message_id)

        see_appeals(user)

        print(players)

    elif call_data == 'see_answer':
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn2 = types.InlineKeyboardButton('⬅️Назад', callback_data='back_to_my_appeals')
        markup.add(btn2)

        bot.send_message(user, f'Ответ администратора:\n <i>{answers[key]}</i>', reply_markup=markup, parse_mode='html')

    elif call_data == 'back_to_my_appeals':
        bot.delete_message(user, call.message.message_id)

    elif call_data == 'add_faq':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Отмена')
        markup.add(btn1)

        bot.send_message(user, 'Напишите вопрос', reply_markup=markup)

        bot.register_next_step_handler(call.message, add_answer_faq)

    elif call_data == 'delete_faq':
        bot.delete_message(user, call.message.message_id)

        markup = types.InlineKeyboardMarkup(row_width=2)
        info_faq = ''
        btns_faq = []

        for i, quest in enumerate(faq.items()):
            delete_choice = '|'.join(['delete_choice', str(quest[0])])
            info_faq += f'\n\n№ {i + 1}: {quest[1][0]}'
            btns_faq.append(types.InlineKeyboardButton(f'{i + 1}', callback_data=delete_choice))

        markup.add(*btns_faq)
        markup.add(types.InlineKeyboardButton('⬅️Назад', callback_data='back_to_admin_list_faq'))

        bot.send_message(user, f'Список FAQ:{info_faq}\n\nВыберите вопрос который хотите удалить', reply_markup=markup)

    elif call_data == 'delete_choice':
        bot.delete_message(user, call.message.message_id)

        delete_num = '|'.join(['delete_num', str(key)])

        markup = types.InlineKeyboardMarkup(row_width=2)

        btn1 = types.InlineKeyboardButton('Нет ✖', callback_data='delete_faq')
        btn2 = types.InlineKeyboardButton('Да ✔', callback_data=delete_num)

        markup.add(btn1, btn2)


        bot.send_message(user, 'Вы действительно хотите удалить данный вопрос?', reply_markup=markup)

    elif call_data == 'delete_num':
        _ = faq.pop(key, None)

        conn = sqlite3.connect('tech_support_database.sql')
        cur = conn.cursor()

        cur.execute("delete from FAQ where count_faq=(?)", (key,))
        conn.commit()

        cur.close()
        conn.close()

        bot.answer_callback_query(call.id, 'Данный вопрос удалён')

        bot.delete_message(user, call.message.message_id)

        list_faq_admin(user)

    elif call_data == 'back_to_admin_list_faq':
        bot.delete_message(user, call.message.message_id)

        list_faq_admin(user)

    elif call_data == 'see_faq':
        bot.delete_message(user, call.message.message_id)

        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('⬅️Назад', callback_data='back_to_user_list_faq')
        markup.add(btn1)

        bot.send_message(user, f'<b>Вопрос:</b> {faq[key][0]}\n<b>Ответ:</b> \n{faq[key][1]}', reply_markup=markup, parse_mode='html')

    elif call_data == 'back_to_user_list_faq':
        bot.delete_message(user, call.message.message_id)

        list_faq_user(user)



if __name__ == '__main__':
    bot.polling(non_stop=True)
