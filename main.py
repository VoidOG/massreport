from pyrogram import Client
import os
from threading import Thread
from colorama import Fore, init

class ReportReason:
    SPAM = "spam"
    VIOLENCE = "violence"
    CHILD_ABUSE = "child_abuse"
    PORNOGRAPHY = "pornography"
    FAKE = "fake"
    ILLEGAL_DRUGS = "illegal_drugs"
    COPYRIGHT = "copyright"
    OTHER = "other"

# Initialize Colorama
init(autoreset=True)

# Replace these with your credentials
API_ID = 28255147  # Replace with your Telegram API ID
API_HASH = "8113960fe67c0cc815e6acce2aefb410"  # Replace with your Telegram API Hash
SESSION_STRINGS = [
    "BQE8lCYAIILy1bqWn_JZB00JGpSlqGV6QCtBdwFBc17rsbGqcBeHrNBUKz0nugHOnMnhVhIUdKilAMr0V5IVjUnUooko1TYo2ps8LbgNhtEJYzU8IXlpUuxEKasB7kmcmn2Z5xXGChzRMkS7-2v6PuPdKGN-az8L_Rp4nVYO8G7eiY7gS6hbxmg3omM6Yq80RKmng27RvAW-wEd5ZHvVm6pbFZRhCmGtlpVV_LMfg5b5kUrT_mylLxUI6h2JC1YK4pnaUDka-LV2G_P2EmuvdDHN6ZdoRs8yG4v98X2Q0jUOTatLWP1vXcCGyQdzYfEVuZ59mS15QZ7emBCOBHCsCY_KqsoAAAAAGIyZUZAA"
]

WELCOME_ART = f"""
{Fore.RED}
.___________. __    __   _______    .___  ___.      ___           _______.     _______.     ___       ______ .______       _______     _______.   
|           ||  |  |  | |   ____|   |   \/   |     /   \         /       |    /       |    /   \     /      ||   _  \     |   ____|   /       |   
`---|  |----`|  |__|  | |  |__      |  \  /  |    /  ^  \       |   (----`   |   (----`   /  ^  \   |  ,----'|  |_)  |    |  |__     |   (----`   
    |  |     |   __   | |   __|     |  |\/|  |   /  /_\  \       \   \        \   \      /  /_\  \  |  |     |      /     |   __|     \   \       
    |  |     |  |  |  | |  |____    |  |  |  |  /  _____  \  .----)   |   .----)   |    /  _____  \ |  `----.|  |\  \----.|  |____.----)   |      
    |__|     |__|  |__| |_______|   |__|  |__| /__/     \__\ |_______/    |_______/    /__/     \__\ \______|| _| `._____||_______|_______/       
                                                                                                                                                  
{Fore.YELLOW}   Mass Reporting Tool by {Fore.RED}The Massacres{Fore.YELLOW} | Join us at {Fore.GREEN}@themassacres
"""


def report_action(session_string, reason, target, target_type, report_count):
    app = Client(session_name=session_string, api_id=API_ID, api_hash=API_HASH, session_string=session_string)

    try:
        app.start()
        print(Fore.GREEN + f"Session started: {session_string[:10]}...")

        for i in range(report_count):
            if target_type == "user":
                app.report_user(target, reason=reason)
            elif target_type == "chat":
                app.report_chat(target, reason=reason)
            elif target_type == "message":
                app.report_message(chat_id=target[0], message_id=target[1], reason=reason)

            print(Fore.YELLOW + f"Report {i + 1}/{report_count} sent successfully from session {session_string[:10]}...")

        app.stop()
        print(Fore.GREEN + f"Session {session_string[:10]} completed successfully!")

    except Exception as e:
        print(Fore.RED + f"Error with session {session_string[:10]}: {e}")


def main():
    os.system("clear")
    print(WELCOME_ART)

    # Input for the target to report
    print(Fore.CYAN + "\nReport Target Options:")
    print(Fore.YELLOW + "1. User (Username or User ID)")
    print(Fore.YELLOW + "2. Chat (Channel or Group ID/Link)")
    print(Fore.YELLOW + "3. Specific Message (Chat ID/Link + Message ID)")
    target_choice = int(input(Fore.CYAN + "\nEnter your choice (1-3): "))

    # Determine the target type
    if target_choice == 1:
        target = input(Fore.CYAN + "Enter Username or User ID: ").strip()
        target_type = "user"
    elif target_choice == 2:
        target = input(Fore.CYAN + "Enter Chat ID or Link: ").strip()
        target_type = "chat"
    elif target_choice == 3:
        chat_id = input(Fore.CYAN + "Enter Chat ID or Link: ").strip()
        message_id = int(input(Fore.CYAN + "Enter Message ID: "))
        target = (chat_id, message_id)
        target_type = "message"
    else:
        print(Fore.RED + "Invalid choice. Exiting.")
        return

  # Select the reason for reporting
print(Fore.CYAN + "\nReport Reasons:")
reasons = [
    ReportReason.SPAM,
    ReportReason.VIOLENCE,
    ReportReason.CHILD_ABUSE,
    ReportReason.PORNOGRAPHY,
    ReportReason.FAKE,
    ReportReason.ILLEGAL_DRUGS,
    ReportReason.COPYRIGHT,
    ReportReason.OTHER,
]

for i, reason in enumerate(reasons, 1):
    print(Fore.YELLOW + f"{i}. {reason.replace('_', ' ').title()}")

reason_choice = int(input(Fore.CYAN + "Select a reason (1-8): "))
reason = reasons[reason_choice - 1]

    # Input for number of reports
    report_count = int(input(Fore.YELLOW + "\nEnter the number of reports (max 10,000): "))
    if report_count > 10000:
        print(Fore.RED + "Exceeded the maximum limit of 10,000. Exiting.")
        return

    # Start reporting with all session strings
    threads = []
    for session_string in SESSION_STRINGS:
        thread = Thread(target=report_action, args=(session_string, reason, target, target_type, report_count))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print(Fore.GREEN + "\nAll reports sent successfully across all sessions!")


if __name__ == "__main__":
    main()
