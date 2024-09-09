import os
from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import (InputReportReasonSpam, InputReportReasonViolence, 
                               InputReportReasonPornography, InputReportReasonOther, 
                               InputReportReasonFake)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
AUTHORIZED_USER_IDS = set(
    map(int, (os.getenv('AUTHORIZED_USER_IDS') or "").split(' '))
)

# Reporting accounts details
REPORTING_ACCOUNTS = [
    {
        'phone': os.getenv('REPORTER_1_PHONE_NUMBER'),
        'api_id': os.getenv('REPORTER_1_API_ID'),
        'api_hash': os.getenv('REPORTER_1_API_HASH')
    },
    {
        'phone': os.getenv('REPORTER_2_PHONE_NUMBER'),
        'api_id': os.getenv('REPORTER_2_API_ID'),
        'api_hash': os.getenv('REPORTER_2_API_HASH')
    }
]

# Conversation states
CHOOSING, REASON, TARGET_INFO, NUM_REPORTS = range(4)

# Predefined reasons mapping
REASONS_MAPPING = {
    'spam': InputReportReasonSpam(),
    'violence': InputReportReasonViolence(),
    'hate_speech': InputReportReasonOther(),  # Since 'Hate Speech' doesn't have a direct mapping, 'Other' is used.
    'sexual_content': InputReportReasonPornography(),
    'harassment': InputReportReasonOther(),  # 'Harassment' can be categorized under 'Other'.
    'fake_account': InputReportReasonFake(),
    'other': InputReportReasonOther(),
}

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
    query = update.callback_query
    query.answer()
    context.user_data['report_type'] = query.data
    
    # Prompt user for reason after selecting the report type
    keyboard = [
        [InlineKeyboardButton("Spam", callback_data='spam')],
        [InlineKeyboardButton("Violence", callback_data='violence')],
        [InlineKeyboardButton("Hate Speech", callback_data='hate_speech')],
        [InlineKeyboardButton("Sexual Content", callback_data='sexual_content')],
        [InlineKeyboardButton("Harassment", callback_data='harassment')],
        [InlineKeyboardButton("Fake Account", callback_data='fake_account')],
        [InlineKeyboardButton("Other", callback_data='other')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"Selected: {query.data}. Choose a reason for reporting:", reply_markup=reply_markup)
    return REASON

def get_reason(update, context):
    query = update.callback_query
    query.answer()
    context.user_data['reason'] = query.data
    
    # Prompt user for target info based on the report type
    if context.user_data['report_type'] == 'report_account':
        query.edit_message_text(text=f"Selected reason: {query.data}. Please provide the target's user ID or username:")
    else:
        query.edit_message_text(text=f"Selected reason: {query.data}. Please provide the target info (username or link):")
    return TARGET_INFO

def handle_target_info(update, context):
    target_info = update.message.text
    context.user_data['target_info'] = target_info
    
    # Prompt user for number of reports
    update.message.reply_text(f"Reporting {context.user_data['target_info']} for {context.user_data['reason']}. How many times do you want to report it?")
    return NUM_REPORTS

def get_num_reports(update, context):
    try:
        num_reports = int(update.message.text)
        if num_reports <= 0:
            raise ValueError
    except ValueError:
        update.message.reply_text("Please enter a valid number of reports.")
        return NUM_REPORTS
    
    context.user_data['num_reports'] = num_reports
    update.message.reply_text(f"Reporting {context.user_data['target_info']} {num_reports} times for {context.user_data['reason']}.")

    # Perform reporting
    for _ in range(num_reports):
        for account in REPORTING_ACCOUNTS:
            report_target(account, context.user_data['report_type'], context.user_data['target_info'], context.user_data['reason'])

    return ConversationHandler.END

def report_target(account, report_type, target_info, reason):
    client = TelegramClient(account['phone'], account['api_id'], account['api_hash'])

    async def perform_reporting():
        await client.start(phone=account['phone'])
        try:
            report_reason = REASONS_MAPPING.get(reason, ReportReason.OTHER)
            
            if report_type == 'report_account':
                await client(functions.account.ReportPeerRequest(
                    peer=target_info,
                    reason=report_reason,
                ))
            elif report_type in ['report_group', 'report_channel']:
                await client(functions.messages.ReportRequest(
                    peer=target_info,
                    reason=report_reason,
                ))
            elif report_type == 'report_message':
                message_link = target_info
                # Extract message ID and chat ID from the message link
                message_id, chat_id = extract_message_and_chat_id(message_link)
                await client(functions.messages.ReportRequest(
                    peer=chat_id,
                    id=[message_id],  # Message ID needs to be passed as a list
                    reason=report_reason,
                ))
        except SessionPasswordNeededError:
            # Handle two-step verification
            print(f"Two-step verification is enabled for {account['phone']}. Please enter your 2SV password.")
            password = input("Enter your 2SV password: ")
            await client.start(password=password)
        finally:
            await client.disconnect()

    with client:
        client.loop.run_until_complete(perform_reporting())

def extract_message_and_chat_id(message_link):
    # Placeholder implementation, needs actual parsing logic
    # Extract message ID and chat ID from the provided message link
    # Example: https://t.me/channel/1234
    # Adjust regex based on the actual message link structure
    try:
        parts = message_link.split('/')
        message_id = int(parts[-1])  # Assuming the last part is the message ID
        chat_id = parts[-2]  # Assuming the second last part is the chat ID or username
        return message_id, chat_id
    except (ValueError, IndexError):
        print("Error: Invalid message link format.")
        return None, None

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
