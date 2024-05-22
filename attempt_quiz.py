"""
Module with methods to attempt to a quiz with a telegram bot
"""
import logging
import random
import pickle
import os
import pymongo
from telegram.constants import ChatAction
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from question_factory import QuestionBool, QuestionChoice, QuestionChoiceSingle, \
    QuestionNumber, QuestionString
from attempt import Attempt

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

db = pymongo.MongoClient(os.environ.get('MONGODB')).quizzes
# Dict to store user data like an attempt instance
userDict = dict()


async def start(update, _):
    """
    Starts a conversation about an attempt at a quiz.
    Welcomes the user and asks for a quiz.
    """
    logger.info('[%s] Attempt initialized', update.message.from_user.username)

    if update.message.from_user.id in userDict:
        # user is in the middle of a quiz and can't attempt a second one
        logger.info('[%s] Attempt canceled because the user is in the middle of a quiz.',
                    update.message.from_user.username)
        await update.message.reply_text(
            "Во время выполнения теста нельзя запускать следующий 😁\n"
            'Если ты хочешь закончить - введи /cancelattempt.'
        )
        return ConversationHandler.END

    await update.message.reply_text(
        'Приветики-пистолетики 😃 Какой тест ты хочешь пройти?\n'
        'Введи номер темы (1-12): '
    )
    return 'ENTER_QUIZ'


async def cancel(update, _):
    """
    Cancels an attempt to a quiz by deleting the users' entries.
    """
    logger.info('[%s] Attempt canceled by user',
                update.message.from_user.username)

    # Remove all user data
    userDict.pop(update.message.from_user.id)
    await update.message.reply_text(
        "Твое тестирование отменено. Увидимся. 🙋‍♂️")
    return ConversationHandler.END


async def enter_quiz(update, context):
    """
    Enters a quiz.
    Try to load a quiz from the input.
    If it succeeded, the bot asks the first question. Otherwise, it asks for another quiz.
    """
    logger.info('[%s] Quiz "%s" entered',
                update.message.from_user.username, update.message.text)

    user_id = update.message.from_user.id

    # name of the quiz is the first word, the creator the from_user by default
    quizname = update.message.text.split()[0]
    quizcreator = "belogolovy"

    # If second word exists, it equals the creator
    if len(update.message.text.split()) > 1:
        quizcreator = update.message.text.split()[1]

    # Bot is typing during database query
    await context.bot.send_chat_action(
        chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    # Quizzes created by the entered user
    user_col = db[quizcreator]
    # Looking for quizname in the database
    quiz_dict = user_col.find_one({'quizname': quizname})
    if quiz_dict is None:
        # couldnt find the quiz
        await update.message.reply_text(
            "Прости, не смог найти тест '{}' 😕 Попробуй снова.".format(
                quizname)
        )
        logger.info('[%s] Couldnt find Quiz %s',
                    update.message.from_user.username, quizname)
        return 'ENTER_QUIZ'

    logger.info('[%s] Found Quiz %s',
                update.message.from_user.username, quizname)
    # if a quiz was found, load it and creates an attempt
    loaded_quiz = pickle.loads(quiz_dict['quizinstance'])
    userDict[user_id] = Attempt(loaded_quiz)
    await update.message.reply_text(
        "Вперед! 🙌 Насладись миром ревматологии с тестом '{}'!\nНо ты можешь отменить наслаждение командой /cancelattempt.".format(
            quizname)
    )

    # Asks first question
    await ask_question(update)
    return 'ENTER_ANSWER'


async def enter_answer(update, _):
    """
    It processes the answer to a question and asks a new question, if possible.
    Otherwise, it prints results.
    """

    user_id = update.message.from_user.id
    user_message = update.message.text
    act_question = userDict[user_id].act_question()

    # If the current question is a multiple-choice question,
    # the bot has to wait for "Enter" to enter the answer.
    if type(act_question) is QuestionChoice and user_message != 'Enter':
        # the current question is a multiple-choice question and not ready to enter

        logger.info('[%s]Insert Answer "%s", Looking for additional answers',
                    update.message.from_user.username, user_message)

        # add answer to list of users' answers
        # TODO What if user answer isnt in possible messages
        userDict[user_id].input_answer(user_message)
        # wait for next answer
        return 'ENTER_ANSWER'
    elif not type(act_question) is QuestionChoice:

        logger.info('[%s] Insert Answer "%s"',
                    update.message.from_user.username, user_message)

        # add answer to list of users' answers
        userDict[user_id].input_answer(user_message)

    # enter the answer of user
    try:
        is_correct, correct_answer = userDict[user_id].enter_answer()
    except AssertionError:
        userDict[user_id].user_answers.clear()
        logger.info("[%s] Something went wrong by entering the answer.",
                    update.message.from_user.username)
        await update.message.reply_text(
            "Прости 😕 Что-то пошло не так при получении твоего ответа. Попробуй снова.")
        return 'ENTER_ANSWER'

    logger.info('[%s] Entered Answer', update.message.from_user.username)

    if userDict[user_id].quiz.show_results_after_question:
        # If creator of the quiz wants the user to see him/her results after the question
        if is_correct:
            await update.message.reply_text("Это верно! 🔥")
        else:
            await update.message.reply_text(
                "Неверно 😕\nПравильный ответ: {}".format(correct_answer))

    if userDict[user_id].has_next_question():
        # check for next question
        await ask_question(update)
        return 'ENTER_ANSWER'

    # no question left
    await update.message.reply_text(
        "Спасибо за участие! ☺️", reply_markup=ReplyKeyboardRemove())
    if userDict[user_id].quiz.show_results_after_quiz:
        # If creator of the quiz wants the user to see him/her results after the quiz
        count = 1
        for is_correct, question in userDict[user_id].user_points:
            await update.message.reply_text(
                "Вопрос {}:\n".format(count)
                + question.question + "\n"
                                      "Ответ" +
                ("правильный 😁" if is_correct else "неправильный. 😕\nПравильный ответ: {}".format(
                    question.correct_answer)),
                reply_markup=ReplyKeyboardRemove())
            count = count + 1

    # Deletes the users entries to closes the attempt
    del userDict[update.message.from_user.id]
    logger.info('[%s] Quitting Quiz', update.message.from_user.username)
    return ConversationHandler.END


async def ask_question(update):
    """
    Formats the keyboard and prints the current question.
    """
    user_id = update.message.from_user.id
    act_question = userDict[user_id].act_question()

    if isinstance(act_question, (QuestionString, QuestionNumber)):
        # String or number question: Use normal Keyboard
        reply_markup = ReplyKeyboardRemove()
    elif isinstance(act_question, QuestionBool):
        # Bool question: Choose between true and false button
        reply_markup = ReplyKeyboardMarkup(
            [['True', 'False']], one_time_keyboard=True)
    elif isinstance(act_question, QuestionChoiceSingle):
        # Single choice question: Choose between possible answers buttons
        list_of_answers = [[el] for el in act_question.possible_answers]
        if act_question.is_random:
            # Shuffle if necessary
            random.shuffle(list_of_answers)
        reply_markup = ReplyKeyboardMarkup(
            list_of_answers, one_time_keyboard=True)
    else:
        # Single choice question: Choose between possible answers buttons
        list_of_answers = [[el] for el in act_question.possible_answers]
        if act_question.is_random:
            # Shuffle if necessary
            random.shuffle(list_of_answers)
        # add termination button
        list_of_answers.append(['Enter'])
        reply_markup = ReplyKeyboardMarkup(
            list_of_answers, one_time_keyboard=False)

    # print question
    await update.message.reply_text(
        '*Вопрос:* ' + act_question.question,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    logger.info('[%s] Printed new question', update.message.from_user.username)
