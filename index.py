"""
Telegram bot to create and attempt to quizzes.
"""

import os
import json
import logging
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, Application
from telegram import Update
# from mongo import mongo_persistence
import create_quiz as createQuiz
import import_quiz as importQuiz
import attempt_quiz as attemptQuiz
import edit_quiz as editQuiz

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# async def handler(event, _):
#     TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
#     application = Application.builder().token(TELEGRAM_TOKEN).build()
#     setup_bot(application)
#
#     try:
#         await application.initialize()
#         await application.process_update(
#             Update.de_json(json.loads(event["body"]), application.bot)
#         )
#         await application.shutdown()
#
#     except Exception as e:
#         print(e)
#         return {'statusCode': 500}
#
#     return {'statusCode': 200, 'body': '!'}


async def print_help(update, _):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Привет! 🙋‍♂️ \n'
    )
    await update.message.reply_text(
        'Что это за бот? 😃\n\n'
        'Этот бот нужен для проходения теста ФОС 31.08.46 Ревматология 2024\n\n'
        'Доступные команды: \n\n'
        '/start: запуск бота, получение описание команд \n\n'
        '/attempt: запустить тестирование \n\n'
        '/rename: переименовать тест \n\n'
        '/remove: удалить тест \n\n'
        'Наслаждайся (если сможешь)! 🥳'
    )


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def setup_bot(updater):
    """Setups the handlers"""
    dispatch = updater

    # start command
    dispatch.add_handler(CommandHandler("start", print_help))
    dispatch.add_handler(CommandHandler("help", print_help))

    # Conversation if the user wants to create a quiz
    create_states = {
        'ENTER_TYPE': [MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_type)],
        'ENTER_QUESTION': [MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_question)],
        'ENTER_ANSWER': [MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_answer)],
        'ENTER_POSSIBLE_ANSWER': [MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_possible_answer)],
        'ENTER_RANDOMNESS_QUESTION': [
            MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_randomness_question)],
        'ENTER_RANDOMNESS_QUIZ': [MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_randomness_quiz)],
        'ENTER_RESULT_AFTER_QUESTION': [
            MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_result_after_question)],
        'ENTER_RESULT_AFTER_QUIZ': [
            MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_result_after_quiz)],
        'ENTER_QUIZ_NAME': [MessageHandler(filters.TEXT & ~filters.COMMAND, createQuiz.enter_quiz_name)],
    }
    create_handler = ConversationHandler(
        entry_points=[CommandHandler('create', createQuiz.start)],
        states=create_states,
        fallbacks=[CommandHandler('cancelCreate', createQuiz.cancel)],
        name='create_handler'
    )
    dispatch.add_handler(create_handler)

    # Conversation if the user wants to attempt a quiz
    attempt_states = {
        'ENTER_QUIZ': [MessageHandler(filters.TEXT & ~filters.COMMAND, attemptQuiz.enter_quiz)],
        'ENTER_ANSWER': [MessageHandler(filters.TEXT & ~filters.COMMAND, attemptQuiz.enter_answer)]
    }
    attempt_handler = ConversationHandler(
        entry_points=[CommandHandler('attempt', attemptQuiz.start)],
        states=attempt_states,
        fallbacks=[CommandHandler('cancelattempt', attemptQuiz.cancel)],
        name='attempt_handler'
    )
    dispatch.add_handler(attempt_handler)

    # Conversation about remove or renaming exisiting quiz
    edit_states = {
        'ENTER_NAME': [MessageHandler(filters.TEXT & ~filters.COMMAND, editQuiz.enter_name_remove)],
        'ENTER_OLD_NAME': [MessageHandler(filters.TEXT & ~filters.COMMAND, editQuiz.enter_old_name)],
        'ENTER_NEW_NAME': [MessageHandler(filters.TEXT & ~filters.COMMAND, editQuiz.enter_new_name)]
    }
    edit_handler = ConversationHandler(
        entry_points=[CommandHandler('rename', editQuiz.start_rename), CommandHandler(
            'remove', editQuiz.start_remove)],
        states=edit_states,
        fallbacks=[CommandHandler('cancelEdit', editQuiz.cancel_edit)],
        name='edit_handler'
    )
    dispatch.add_handler(edit_handler)

    # import COMMAND
    import_states = {
        'ENTER_NAME': [MessageHandler(filters.TEXT & ~filters.COMMAND, importQuiz.enter_quiz_name)],
        'LOAD_FILE': [MessageHandler(filters.TEXT & ~filters.COMMAND, importQuiz.cancel)],
        'ENTER_QUIZ_NAME': [MessageHandler(filters.TEXT & ~filters.COMMAND, importQuiz.enter_quiz_name)]
    }
    import_handler = ConversationHandler(
        entry_points=[CommandHandler('import', importQuiz.start)],
        states=import_states,
        fallbacks=[CommandHandler('cancelImport', importQuiz.cancel)],
        name='import_handler'
    )
    dispatch.add_handler(import_handler)

    # excel file command
    dispatch.add_handler(MessageHandler(filters.Document.ALL, importQuiz.handle_excel_file))

    # log all errors
    dispatch.add_error_handler(error)


if __name__ == '__main__':
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    WEBHOOK = os.environ['WEBHOOK']

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    setup_bot(application)

    application.run_webhook(
        listen="https://"+WEBHOOK,
        port=8443
    )
    application.setWebhook(WEBHOOK + TELEGRAM_TOKEN)

