from pyzeebe import ZeebeWorker
import re

banned_words = ["hate", "violence", "nsfw", "fake", "scam"]
banned_categories = ["health", "finance"]

def register_tasks(worker: ZeebeWorker):
    
    @worker.task(task_type="check-eligibility")
    def check_eligibility(monthly_views: int, subscribers: int):
        eligibility_status = None
        if monthly_views >= 4000 and subscribers >= 1000:
            eligibility_status = True
            print(f"Number of monthly_views: {monthly_views}, Number of subscribers: {subscribers}")
        else:
            eligibility_status = False
            print(f"not enough subscribers or monthly views")
        return {"eligibility_status": eligibility_status}

    @worker.task(task_type="verify-compliance")
    def verify_compliance(creator_name: str, channel_name: str, channel_description: str, channel_category: str):
        content = f"{creator_name} {channel_name} {channel_description}".lower()

        # Regex to look only for separate words in banned words
        pattern = r"\b(" + "|".join(banned_words) + r")\b"
        has_banned_word = bool(re.search(pattern, content))
        
        category_ok = channel_category.lower() not in banned_categories

        compliance_status = not has_banned_word and category_ok

        # Logs
        if has_banned_word:
            print(f"❌ Banned word found in content: {content}")
        if not category_ok:
            print(f"❌ Category '{channel_category}' is restricted")
        if compliance_status:
            print("✅ Channel is compliant")
    
        return {"compliance_status": compliance_status}
