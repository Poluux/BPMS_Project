from pyzeebe import ZeebeWorker
import re
from pathlib import Path
import requests

banned_words = ["hate", "violence", "nsfw", "fake", "scam"]
banned_categories = ["health", "finance"]

def register_tasks(worker: ZeebeWorker):

    @worker.task(task_type="check-eligibility")
    def check_eligibility(monthly_views: int, subscribers: int):
        eligibility_status = monthly_views >= 4000 and subscribers >= 1000
        print(f"Monthly views: {monthly_views}, Subscribers: {subscribers}, Eligible: {eligibility_status}")
        return {"eligibility_status": eligibility_status}

    @worker.task(task_type="verify-compliance")
    def verify_compliance(creator_name: str, channel_name: str, channel_description: str, channel_category: str):
        content = f"{creator_name} {channel_name} {channel_description}".lower()
        pattern = r"\b(" + "|".join(banned_words) + r")\b"
        has_banned_word = bool(re.search(pattern, content))
        category_ok = channel_category.lower() not in banned_categories
        compliance_status = not has_banned_word and category_ok
        if has_banned_word:
            print(f"Banned word found: {content}")
        if not category_ok:
            print(f"Category '{channel_category}' restricted")
        if compliance_status:
            print("✅ Channel is compliant")
        return {"compliance_status": compliance_status}

    @worker.task(task_type="sendRecommendation.result")
    def process_sendgrid_result(subject: str, sendgrid_result: dict = None):
        if not subject or subject.strip() == "":
            print("[Script Task] Subject vide ! Renvoi vers Write recommendations.")
            return {
                "emailStatus": "retry",
                "emailMessageId": None
            }

        status = "failed"
        message_id = None

        if sendgrid_result is not None and isinstance(sendgrid_result, dict) and sendgrid_result.get("status") == "success":
            status = "success"
            message_id = sendgrid_result.get("message_id")

        print(f"[Script Task] Email send status: {status}, message_id: {message_id}")
        return {
            "emailStatus": status,
            "emailMessageId": message_id
        }
    
    # Script to check AdSense link is good + call an API to get the date + create file with creator information
    @worker.task(task_type="check-AdSense")
    def checkAdSense_callDateWebAPI_createFile(full_name: str, card_number: str, activate_checkbox: bool, creator_name: str, monthly_views: int, subscribers: int):
        adSense_status = None
        current_date = None

        # Checking information
        if(full_name != None and card_number != None and activate_checkbox == True):
            adSense_status = True
            print("All fields are completed and checkboxe is checked, Monetization is activated")
        else:
            adSense_status = False
            print("Some fields are empty or the checkboxe was not checked")

        # Web API call to get current date
        try:
            response = requests.get("http://worldclockapi.com/api/json/utc/now")
            response.raise_for_status()
            data = response.json()
            current_date = data.get("currentDateTime")
        except Exception as e:
            print(f"❌ Error fetching date: {e}")

        # Creation of file output
        content = (
        f"Creator: {creator_name}\n"
        f"Monthly Views: {monthly_views}\n"
        f"Subscribers: {subscribers}\n"
        f"Date: {current_date}\n"
        )

        downloads_path = Path.home() / "Downloads"
        date_for_filename = current_date.replace(":", "-") if current_date else "nodate"
        file_name = f"report_{creator_name}_{date_for_filename}.txt"
        file_path = downloads_path / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"File created successfully {file_path}")
        return {"adSense_status": adSense_status, "date": current_date}

        
