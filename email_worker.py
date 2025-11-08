import os
import asyncio
from pyzeebe import ZeebeWorker, create_camunda_cloud_channel
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Connexion à Camunda Cloud
    channel = create_camunda_cloud_channel(
        client_id=os.environ["ZEEBE_CLIENT_ID"],
        client_secret=os.environ["ZEEBE_CLIENT_SECRET"],
        cluster_id=os.environ["ZEEBE_ADDRESS"].split(".")[0],
        region="bru-2"
    )

    worker = ZeebeWorker(channel)

    @worker.task(task_type="generate_email")
    def generate_email(creator_name: str):
        email_text = f"""
Dear {creator_name},

Here are the Guidelines for Activating AdSense on Your YouTube Channel:

1. Eligibility Requirements
• Your channel must have at least 1,000 subscribers.
• You need 4,000 watch hours in the past 12 months.
• Your content must comply with YouTube’s Community Guidelines and Terms of Service.

2. Linking an AdSense Account
• Go to your YouTube Studio → Monetization tab.
• Click on “Start” under AdSense setup.
• Sign in to your existing AdSense account, or create a new one.

3. Content Guidelines
• Ensure your videos are original.
• Avoid copyrighted material unless you have proper licenses.
• Thumbnails and titles should be accurate and appropriate.

4. Channel Requirements
• Your channel must be active for at least 30 days.
• Verify your account via email.
• Ensure your contact info is up-to-date.

5. Review Process
• After linking AdSense, the YouTube Staff will review your channel.
• You may receive approval or rejection with comments.
• Address any issues noted to meet the monetization criteria.
        """

        # Créer le tableau attendu par le connecteur SendGrid
        email_content = [
            {
                "type": "text/plain",
                "value": email_text
            }
        ]

        print(f"Generated email for {creator_name}")
        return {"email_content": email_content}

    print("Email worker started")
    await worker.work()

if __name__ == "__main__":
    asyncio.run(main())
