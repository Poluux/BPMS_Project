from pyzeebe import ZeebeWorker
import re

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

from pyzeebe import ZeebeWorker

def register_tasks(worker: ZeebeWorker):

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
