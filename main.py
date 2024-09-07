import os
from dotenv import load_dotenv
from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonViolence,
    InputReportReasonPornography,
    InputReportReasonOther,
    InputReportReasonHateSpeech,
    InputReportReasonHarassment,
    InputReportReasonFakeAccount,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

# Load environment variables
load_dotenv()

# Constants
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
SESSION_NAME = 'session_name'  # Change this as needed

# Authorized User IDs
AUTHORIZED_USER_IDS = {123456789, 987654321}  # Replace with actual user IDs

# Conversation states
CHOOSING, REASON, TARGET_INFO, NUM_REPORTS = range(4)

# Predefined reasons mapping
REASONS_MAPPING = {
    'spam': InputReportReasonSpam(),
    'violence': InputReportReasonViolence(),
    'pornography': InputReportReasonPornography(),
    'hate_speech': InputReportReasonHateSpeech(),
    'harassment': InputReportReasonHarassment(),
    'fake_account': InputReportReasonFakeAccount(),
    'other': InputReportReasonOther(),
}

# Define reporter credentials
REPORTER_CREDENTIALS = [
    {
        'api_id': os.getenv('API_ID_1'),
        'api_hash': os.getenv('API_HASH_1'),
        'phone_number': os.getenv('PHONE_NUMBER_1'),
        'phone_code_hash': os.getenv('PHONE_CODE_HASH_1'),
        'phone_code': os.getenv('PHONE_CODE_1'),
        'auth_code': os.getenv('AUTH_CODE_1'),
    },
    # Add more accounts as needed
]

async def login(client, credentials):
    await client.connect()
    
    if not await client.is_user_authorized():
        sent_code = await client.send_code_request(credentials['phone_number'])
        phone_code_hash = sent_code.phone_code_hash
        await client.sign_in(credentials['phone_number'], credentials['phone_code'], phone_code_hash)
        
        # Handle two-step verification if enabled
        try:
            await client.sign_in(password=credentials['auth_code'])
        except SessionPasswordNeededError:
            password = input(f"Two-step verification enabled for {credentials['phone_number']}. Enter your password: ")
            await client.sign_in(password=password)

async def report_target(credentials, report_type, target_info, reason):
    client = TelegramClient(f'session_{credentials["phone_number"]}', credentials['api_id'], credentials['api_hash'])
    
    async def perform_reporting():
        await login(client, credentials)
        try:
            if report_type in ['report_account', 'report_group', 'report_channel']:
                await client(functions.messages.ReportRequest(
                    peer=target_info,
                    reason=reason
                ))
            elif report_type == 'report_message':
                message_id, chat_id = extract_message_and_chat_id(target_info)
                await client(functions.messages.ReportRequest(
                    peer=chat_id,
                    id=[message_id],
                    reason=reason
                ))
        except SessionPasswordNeededError:
            password = input(f"Two-step verification required for {credentials['phone_number']}. Enter your password: ")
            await client.sign_in(password=password)
            # Retry reporting
            await perform_reporting()
        finally:
            await client.disconnect()

    with client:
        client.loop.run_until_complete(perform_reporting())

def extract_message_and_chat_id(message_link):
    # Implement extraction logic here
    message_id = 0
    chat_id = 0
    return message_id, chat_id

def start(update, context):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USER_IDS:
        update.message.reply_text("You are not authorized to use this bot.")
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("Report Telegram Account", callback_data='report_account')],
        [InlineKeyboardButton("Report Group", callback_data='report_group')],
        [InlineKeyboardButton("Report Channel", callback_data='report_channel')],
        [InlineKeyboardButton("Report Specific Message", callback_data='report_message')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Welcome to Cenzo Mass Report Tool! Please choose what you want to report:', reply_markup=reply_markup)
    return CHOOSING

def choose_report_type(update, context):
    user_id = update.callback_query.from_user.id
    if user_id not in AUTHORIZED_USER_IDS:
        update.callback_query.answer()
        update.callback_query.message.reply_text("You are not authorized to use this bot.")
        return ConversationHandler.END
    
    query = update.callback_query
    query.answer()
    context.user_data['report_type'] = query.data
    
    keyboard = [
        [InlineKeyboardButton("Spam", callback_data='spam')],
        [InlineKeyboardButton("Violence", callback_data='violence')],
        [InlineKeyboardButton("Pornography", callback_data='pornography')],
        [InlineKeyboardButton("Hate Speech", callback_data='hate_speech')],
        [InlineKeyboardButton("Harassment", callback_data='harassment')],
        [InlineKeyboardButton("Fake Account", callback_data='fake_account')],
        [InlineKeyboardButton("Other", callback_data='other')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"Selected: {query.data}. Choose a reason for reporting:", reply_markup=reply_markup)
    return REASON

def get_reason(update, context):
    user_id = update.callback_query.from_user.id
    if user_id not in AUTHORIZED_USER_IDS:
        update.callback_query.answer()
        update.callback_query.message.reply_text("You are not authorized to use this bot.")
        return ConversationHandler.END
    
    query = update.callback_query
    query.answer()
    
    reason_input = query.data
    context.user_data['reason'] = REASONS_MAPPING.get(reason_input, InputReportReasonOther())
    
    if context.user_data['report_type'] == 'report_account':
        query.edit_message_text(text=f"Selected reason: {reason_input}. Please provide the target's user ID or username:")
    else:
        query.edit_message_text(text=f"Selected reason: {reason_input}. Please provide the target info (username or link):")
    
    return TARGET_INFO

def handle_target_info(update, context):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USER_IDS:
        update.message.reply_text("You are not authorized to use this bot.")
        return ConversationHandler.END
    
    target_info = update.message.text
    context.user_data['target_info'] = target_info
    
    update.message.reply_text(f"Reporting {context.user_data['target_info']} for {context.user_data['reason']}. How many times do you want to report it?")
    return NUM_REPORTS

def get_num_reports(update, context):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USER_IDS:
        update.message.reply_text("You are not authorized to use this bot.")
        return ConversationHandler.END
    
    try:
        num_reports = int(update.message.text)
        if num_reports <= 0:
            raise ValueError
    except ValueError:
        update.message.reply_text("Please enter a valid number of reports.")
        return NUM_REPORTS
    
    context.user_data['num_reports'] = num_reports
    
    update.message.reply_text(f"Reporting {context.user_data['target_info']} {num_reports} times for {context.user_data['reason']}.")
    
    # Handle reporting logic using multiple accounts
    for credentials in REPORTER_CREDENTIALS:
        report_target(credentials, context.user_data['report_type'], context.user_data['target_info'], context.user_data['reason'])
    
    return ConversationHandler.END

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    
    dp = updater.dispatcher
    
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [CallbackQueryHandler(choose_report_type)],
            REASON: [CallbackQueryHandler(get_reason)],
            TARGET_INFO: [MessageHandler(Filters.text & ~Filters.command, handle_target_info)],
            NUM_REPORTS: [MessageHandler(Filters.text & ~Filters.command, get_num_reports)],
        },
        fallbacks=[CommandHandler('start', start)],
    )
    
    dp.add_handler(conversation_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
