import os
from telethon import TelegramClient, functions
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import ReportReason
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

# Constants
API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# Authorized User IDs (add your user IDs here)
AUTHORIZED_USER_IDS = {123456789, 987654321}

# Reporting accounts details
REPORTING_ACCOUNTS = [
    {
        'phone': 'YOUR_REPORTER_1_PHONE_NUMBER',
        'api_id': 'YOUR_REPORTER_1_API_ID',
        'api_hash': 'YOUR_REPORTER_1_API_HASH'
    },
    {
        'phone': 'YOUR_REPORTER_2_PHONE_NUMBER',
        'api_id': 'YOUR_REPORTER_2_API_ID',
        'api_hash': 'YOUR_REPORTER_2_API_HASH'
    }
]

# Conversation states
CHOOSING, REASON, TARGET_INFO, NUM_REPORTS = range(4)

# Predefined reasons mapping
REASONS_MAPPING = {
    'spam': ReportReason.SPAM,
    'violence': ReportReason.VIOLENCE,
    'hate_speech': ReportReason.HATE_SPEECH,
    'sexual_content': ReportReason.SEXUAL_CONTENT,
    'harassment': ReportReason.HARASSMENT,
    'fake_account': ReportReason.FAKE_ACCOUNT,
    'other': ReportReason.OTHER,
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
                # Extract message ID and chat ID from the link
                message_id, chat_id = extract_message_and_chat_id(message_link)
                await client(functions.messages.ReportRequest(
                    peer=chat_id,
                    id=message_id,
                    reason=report_reason
                ))
        except SessionPasswordNeededError:
            # Handle two-step verification
            password = input("Two-step verification is enabled. Enter your 2SV password: ")
            await client.start(password=password)
            # Retry reporting after successful login
        finally:
            await client.disconnect()

    with client:
        client.loop.run_until_complete(perform_reporting())

def extract_message_and_chat_id(message_link):
    # Implement extraction of message ID and chat ID from the link
    # This is a placeholder; implement actual extraction logic
    message_id = 0
    chat_id = 0
    return message_id, chat_id

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
