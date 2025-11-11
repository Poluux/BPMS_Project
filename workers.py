from pyzeebe import ZeebeWorker 
import re
from pathlib import Path
import requests
from pyzeebe.errors import ZeebeError


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
        print(f"✅ Compliance result: {compliance_status}")
        return {"compliance_status": compliance_status}
    

    @worker.task(task_type="sendRecommendation.result")
    def process_sendgrid_result(subject: str, sendgrid_result: dict = None):
        if not subject or subject.strip() == "":
            print("[Script Task] Subject vide ! Redirection vers Error End Event.")
            return {"subject_status": "empty"}  # renvoie une chaîne de caractères

        print("[Script Task] Subject valide. Envoi normal.")
        return {"subject_status": "ok"}




    @worker.task(task_type="check-AdSense")
    def checkAdSense_callDateWebAPI_createFile(full_name: str, card_number: str, activate_checkbox: bool, creator_name: str, monthly_views: int, subscribers: int):
        adSense_status = True if (full_name and card_number and activate_checkbox) else False
        if adSense_status:
            print("✅ All fields complete. Monetization activated.")
        else:
            print("❌ Some fields missing or checkbox unchecked.")
        current_date = None
        try:
            response = requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC", timeout=5)
            response.raise_for_status()
            current_date = response.json().get("datetime")
        except Exception as e:
            print(f"❌ Error fetching date: {e}")
        content = (f"Creator: {creator_name}\nMonthly Views: {monthly_views}\nSubscribers: {subscribers}\nDate: {current_date}\n")
        downloads_path = Path.home() / "Downloads"
        date_for_filename = current_date.replace(":", "-") if current_date else "nodate"
        file_name = f"report_{creator_name}_{date_for_filename}.txt"
        file_path = downloads_path / file_name
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 File created successfully: {file_path}")
        return {"adSense_status": adSense_status, "date": current_date}
