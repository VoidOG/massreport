import asyncio
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

# Constants
API_ID = '23459191'
API_HASH = 'd5f3a01c7bcb41aa1214808b5818c109'
BOT_TOKEN = '7240682346:AAF6gZNwrO3CPLBPYYtg0yiEPxZVTqoJut0'

# Authorized User IDs
AUTHORIZED_USER_IDS = {6663845789, 1110013191, 6698364560}

# Reporting accounts details with string sessions
REPORTING_ACCOUNTS = [
    {
        'session_string': '1BVtsOHwBu4Sep8EoDdbaw1b_tYuq_RtU-mtyLOAUPQvzJqXVEphbcIxF2aq9LrzGl2e1EdEq0eiJfcCVa3vl6YGaTjGoEaMkOjlwP2rWv3l9NOPxms5CIjDICgRVmJXDVO-q-viBftmdqxj-XIpe-77PGPwrcTC8Ayu0t3IISbIpiNBkb9lqHuAxNtyeBLYRVHHRnTx9id3sKiUKEkC0pdg5tUMEJAVcXGleVOgHVxud70kHyegfz8zGyfMXYqWPe9qtjwwoVRQHHPPuqCdCcyheKuYlP8DJD-mdN8hmwYQH7WyvPd3_ziHjftwxkXFuSNpZ9nM3QNgxaYJDbM2tEr3Bbt22zTo=',  # Replace with actual string session
        'api_id': '23459191',
        'api_hash': 'd5f3a01c7bcb41aa1214808b5818c109'
    },
    {
        'session_string': '1BVtsOK8Bu7x0YluVcvaP91cRaJz7hDz-IoJDcwj2cGNIa3srai-9TA-pGFZgvkS9svr4S0pkJEKG5rWVN7itYVHDHeiO_k91JKrtMrNDR0FI0roypGz81jrK6hb4bvxHYxkHiRSu3cvWmZtqAYiJTh7cbR5XH3jjFyAV2xQJ8q29fUdSNhYpEfNtQCOQYACQr0pTFIucJLebLtpyt0AnSDpUhoyf9mVPv3fZ_z5YNozTIPG3A4NIhZZ-NvBYbh57Pe3m6XJyTryDvT2NoDlupR7-G0WpBnHsRgM2lc0uvN4Nsmp2jjkq2lfSQ8J4rcgLjlJ0BNG2kQ5jtoVUg6naNcikRyBvsps=',  # Replace with actual string session
        'api_id': '25162649' ,
        'api_hash': '2ec36ea724f3b846f217a7677e3b5cfd'
    }
]

# Conversation states
CHOOSING, REASON, TARGET_INFO, NUM_REPORTS = range(4)

# Predefined reasons mapping
REASONS_MAPPING = {
    'spam': 'spam',
    'violence': 'violence',
    'hate_speech': 'hate_speech',
    'sexual_content': 'sexual_content',
    'harassment': 'harassment',
    'fake_account': 'fake_account',
    'other': 'other',
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
    
    if context.user_data['report_type'] == 'report_account':
        query.edit_message_text(text=f"Selected reason: {query.data}. Please provide the target's user ID or username:")
    else:
        query.edit_message_text(text=f"Selected reason: {query.data}. Please provide the target info (username or link):")
    return TARGET_INFO

def handle_target_info(update, context):
    target_info = update.message.text
    context.user_data['target_info'] = target_info
    
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
    
    # Perform reporting asynchronously
    asyncio.run(report_targets(context.user_data['report_type'], context.user_data['target_info'], context.user_data['reason'], context.user_data['num_reports']))

    return ConversationHandler.END

async def report_targets(report_type, target_info, reason, num_reports):
    for i in range(num_reports):
        for account in REPORTING_ACCOUNTS:
            await report_target(account, report_type, target_info, reason)
            print(f"{i * len(REPORTING_ACCOUNTS) + REPORTING_ACCOUNTS.index(account) + 1} report(s) sent")
    print("Reporting completed.")

async def report_target(account, report_type, target_info, reason):
    client = TelegramClient(StringSession(account['session_string']), account['api_id'], account['api_hash'])

    async def perform_reporting():
        await client.start()
        try:
            if report_type == 'report_account':
                await client(functions.account.ReportPeerRequest(
                    peer=target_info,
                    reason=REASONS_MAPPING.get(reason, 'other'),
                ))
            elif report_type in ['report_group', 'report_channel']:
                await client(functions.messages.ReportRequest(
                    peer=target_info,
                    reason=REASONS_MAPPING.get(reason, 'other'),
                ))
            elif report_type == 'report_message':
                message_id, chat_id = extract_message_and_chat_id(target_info)
                await client(functions.messages.ReportRequest(
                    peer=chat_id,
                    id=message_id,
                    reason=REASONS_MAPPING.get(reason, 'other'),
                ))
        except SessionPasswordNeededError:
            password = input("Two-step verification is enabled. Enter your 2SV password: ")
            await client.start(password=password)
            await perform_reporting()  # Retry after login
        finally:
            await client.disconnect()

    await perform_reporting()

def extract_message_and_chat_id(message_link):
    # Implement extraction of message ID and chat ID from the link
    # This is a placeholder; implement actual extraction logic
    message_id = 123456  # Example message ID
    chat_id = 654321  # Example chat ID
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
