from pyzeebe import ZeebeWorker 
import re
from pathlib import Path
import requests
from pyzeebe.errors import ZeebeError
import mysql.connector
from pyzeebe import ZeebeClient, create_camunda_cloud_channel
import uuid
import os
from email.message import EmailMessage
import smtplib
import asyncio


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



    """"
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

        """
    

    @worker.task(task_type="check-AdSense")
    def checkAdSense_callDateWebAPI_createFile(
        full_name: str,
        textfield_3f52r: str,
        number_8rp7aj: int,
        select_jepknc: str,
        card_number: str,
        activate_checkbox: bool
    ):
        from pathlib import Path
        import requests
        import mysql.connector
        from datetime import datetime

        print(f"Variables reçues : full_name={full_name}, firstname={textfield_3f52r}, age={number_8rp7aj}, lang={select_jepknc}, iban={card_number}, checkbox={activate_checkbox}")

        # ---- Vérification des champs ----
        def is_filled(value):
            return value is not None and str(value).strip() != ""

        all_filled = all([
            is_filled(full_name),
            is_filled(textfield_3f52r),
            is_filled(number_8rp7aj),
            is_filled(card_number)
        ])

        if not all_filled:
            print("❌ Certains champs du formulaire sont vides.")
            return {"adSense_status": False, "reason": "missing_fields"}

        if not activate_checkbox:
            print("❌ La case 'Activate AdSense' n’est pas cochée.")
            return {"adSense_status": False, "reason": "checkbox_unchecked"}

        # ---- Vérification IBAN unique ----
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="camunda_user",
                password="mdp_camunda",
                database="BpmnDataBase"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM adsense_form WHERE iban_number = %s", (card_number,))
            if cursor.fetchone()[0] > 0:
                cursor.close()
                conn.close()
                print(f"❌ IBAN déjà existant : {card_number}")
                return {"adSense_status": False, "reason": "iban_exists"}
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            print(f"⚠️ Erreur MySQL : {err}")
            return {"adSense_status": False, "reason": "db_error"}

        print("✅ Toutes les conditions sont remplies. AdSense activé.")

        # ---- Récupération sécurisée de la date ----
        try:
            response = requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC", timeout=5)
            response.raise_for_status()
            data = response.json()
            current_date = data.get("datetime")
            if not current_date:
                raise ValueError("Date field empty")
        except Exception as e:
            print(f"⚠️ Impossible de récupérer la date via l'API, fallback à la date locale. Détail: {e}")
            current_date = datetime.utcnow().isoformat()  # UTC fallback

        # ---- Création du fichier de log ----
        safe_date = current_date.replace(":", "-")  # pour le nom de fichier
        downloads_path = Path.home() / "Downloads"
        file_name = f"report_{full_name}_{safe_date}.txt"
        file_path = downloads_path / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                f"Full Name: {full_name}\n"
                f"First Name: {textfield_3f52r}\n"
                f"Age: {number_8rp7aj}\n"
                f"Language: {select_jepknc}\n"
                f"IBAN: {card_number}\n"
                f"Date: {current_date}\n"
            )

        print(f"📄 Fichier créé : {file_path}")

        # ---- Retour pour la gateway ----
        return {"adSense_status": True, "date": current_date}


    @worker.task(task_type="insert-into-db")
    def insert_into_db(full_name: str, textfield_3f52r: str, number_8rp7aj: int, select_jepknc: str, card_number: str):
        """
        Insère dans la base MySQL toutes les infos du formulaire AdSense.
        Le champ activate_checkbox n'est pas stocké.
        """
        try:
            # Connexion MySQL
            conn = mysql.connector.connect(
                host="localhost",
                user="camunda_user",
                password="mdp_camunda",
                database="BpmnDataBase"
            )

            cursor = conn.cursor()

            # Requête SQL
            sql = """
                INSERT INTO adsense_form (surname, firstname, age, language, iban_number)
                VALUES (%s, %s, %s, %s, %s)
            """

            values = (full_name, textfield_3f52r, number_8rp7aj, select_jepknc, card_number)

            cursor.execute(sql, values)
            conn.commit()

            print(f"✅ Data inserted: {values}")

            cursor.close()
            conn.close()

            return {"db_status": "success"}

        except mysql.connector.Error as err:
            print(f"❌ Database error: {err}")
            return {"db_status": "error", "error_msg": str(err)}
        

    @worker.task(task_type="submit_form")
    async def submit_form(formId: str = None, **form_data):
        # Génération d'un formId si absent
        if not formId:
            formId = str(uuid.uuid4())

        print(f"🚀 Envoi du message pour Pool 2 avec formId={formId}")
        print(f"📦 Données transmises : {form_data}")

        # Création du client Zeebe
        channel = create_camunda_cloud_channel(
            client_id=os.environ["ZEEBE_CLIENT_ID"],
            client_secret=os.environ["ZEEBE_CLIENT_SECRET"],
            cluster_id=os.environ["ZEEBE_ADDRESS"].split(".")[0],
            region="bru-2"
        )
        client = ZeebeClient(channel)

        # Publication du message
        await client.publish_message(
            name="form_submitted",   # messageRef du start event de Pool 2
            correlation_key=formId,  # clé de corrélation
            variables=form_data      # variables du formulaire
        )

        print("✅ Message envoyé à Pool 2 avec succès.")
        return {"pool2_started": True, "formId": formId}
    

    @worker.task(task_type="email_sent")
    async def send_email_task(
        formId: str,
        creator_email: str,
        subject: str = "Votre formulaire a été traité",
        body: str = "Bonjour, votre formulaire a bien été traité."
    ):
        print(f"📧 Envoi du mail pour formId={formId} à {creator_email}")

        try:
            # --- Envoi de l'email ---
            msg = EmailMessage()
            msg['From'] = os.environ['EMAIL_SENDER']
            msg['To'] = creator_email
            msg['Subject'] = subject
            msg.set_content(body)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(os.environ['EMAIL_SENDER'], os.environ['EMAIL_PASSWORD'])
                smtp.send_message(msg)

            print("✅ Mail envoyé avec succès")

        except Exception as e:
            print(f"❌ Erreur lors de l'envoi du mail : {e}")
            raise e  # retry automatique par Zeebe

        # --- Publier un message de confirmation vers Pool 1 ---
        channel = create_camunda_cloud_channel(
            client_id=os.environ["ZEEBE_CLIENT_ID"],
            client_secret=os.environ["ZEEBE_CLIENT_SECRET"],
            cluster_id=os.environ["ZEEBE_ADDRESS"].split(".")[0],
            region="bru-2"
        )
        client = ZeebeClient(channel)

        await client.publish_message(
            name="mail_sent_confirmation",   # doit correspondre au message attendu par Pool 1
            correlation_key=formId,          # identifie l'instance de Pool 1
            variables={"status": "done"}     # optionnel, juste pour signaler
        )

        print(f"🔄 Message 'mail_sent_confirmation' envoyé à Pool 1 pour formId={formId}")
        return {"email_status": "sent", "formId": formId}
