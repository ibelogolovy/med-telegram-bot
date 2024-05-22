"""
Module with methods to create a quiz with a telegram bot
"""

import openpyxl
import logging
import pickle
import pymongo
import os
from telegram.constants import ChatAction
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ConversationHandler
from telegram._replykeyboardremove import ReplyKeyboardRemove
from quiz import Quiz
from question_factory import QuestionBool, QuestionChoice, \
    QuestionChoiceSingle, QuestionNumber, QuestionString

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

db = pymongo.MongoClient(os.environ.get('MONGODB')).quizzes

dict_question_types = {
    5: QuestionNumber,
    4: QuestionString,
    3: QuestionBool,
    2: QuestionChoice,
    1: QuestionChoiceSingle
}

# Dict with user data like a quiz instance
userDict = dict()


async def start(update, _):
    """
    Функция для обработки команды /start
    """
    keyboard = [[KeyboardButton("Отправить Excel файл")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Отправьте мне Excel файл.", reply_markup=reply_markup)

    return ConversationHandler.END


# Функция для обработки отправки Excel файла
async def handle_excel_file(update, context):
    file = context.bot.get_file(update.message.document.file_id)
    file.download("received_file.xlsx")

    # Чтение данных из файла
    wb = openpyxl.load_workbook("received_file.xlsx")
    sheet = wb.active

    # Query for question with input name
    user_col = db[update.message.from_user.username]

    questions_by_type = dict()

    # Парсинг данных
    for row in sheet.iter_rows(values_only=True):
        QuestionType = dict_question_types[row[1]]

        # Формируем ответы
        answers = ''
        possible_answers = []
        for x in range(3, 10):
            val = str(row[x])
            if (str(row[x]).startswith('*')):
                answers += '|' + val[1:]
            elif (row[x] is not None):
                possible_answers.append(row[x])

        questionInstance = QuestionType(row[2], answers[1:])

        # Add possible answers to question
        for answer in possible_answers:
            questionInstance.add_possible_answer(answer)

        if str(row[0]) in questions_by_type:
            questions_by_type[str(row[0])].append(questionInstance)
        else:
            questions_by_type[str(row[0])] = [questionInstance]

        logger.info('[%s] Process question "%s"',
                    update.message.from_user.username, row[2])

    for key, value in questions_by_type.items():
        # Init Quiz for user
        quiz = Quiz(update.message.from_user.username)
        # Add questions
        for q in value:
            quiz.add_question(q)
        # Insert Quiz with quizname in database
        user_col.insert_one({'quizname': key, 'quizinstance': pickle.dumps(quiz)})

    await update.message.reply_text(
        "Ура! 🥳 Данные сохранены.",
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info('[%s] Quiz saved as "%s"',
                update.message.from_user.username, update.message.text)

    return ConversationHandler.END


async def cancel(update, _):
    """
    Cancels a creation ofa quiz by deleting the users' entries.
    """
    logger.info('[%s] Import canceled by user',
                update.message.from_user.username)

    # Delete user data
    userDict.pop(update.message.from_user.id)
    await update.message.reply_text(
        "I canceled the creation process. See you next time. 🙋‍♂️",
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def enter_quiz_name(update, context):
    """
    After entering the name of the quiz, it looks up if the quiz name is occupied.
    Otherwise is saves the quiz.
    """

    logger.info('[%s] Completed quiz creation',
                update.message.from_user.username)
    user_id = update.message.from_user.id
    quizname = update.message.text

    # Bot is typing during database query
    context.bot.send_chat_action(
        chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    # Query for question with input name
    user_col = db[update.message.from_user.username]
    if not user_col.find_one({'quizname': quizname}) is None:
        # Quiz with quizname already exists
        await update.message.reply_text(
            "Sorry. You already have a quiz named {} 😕\nPlease try something else".format(
                quizname)
        )
        logger.info('[%s] Quiz with name "%s" already exists',
                    update.message.from_user.username, update.message.text)

        return 'ENTER_QUIZ_NAME'

    # Insert Quiz with quizname in database
    await user_col.insert_one(
        {'quizname': quizname, 'quizinstance': pickle.dumps(userDict[user_id]['quiz'])})
    await update.message.reply_text(
        "Great! 🥳 I saved your new quiz."
        "You can attempt to it by the name {}.".format(quizname),
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info('[%s] Quiz saved as "%s"',
                update.message.from_user.username, update.message.text)
    # Delete user data
    userDict.pop(update.message.from_user.id)
    return ConversationHandler.END
