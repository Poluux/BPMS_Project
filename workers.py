#!/usr/bin/env python3
"""
Worker Camunda 8 – Pool1 / Pool2
Gère toutes les tâches (check-eligibility, verify-compliance, check-AdSense,
insert-into-db, submit_form, email_sent, send_pool2_form, etc.)
Envoi des e-mails via l'API SendGrid (pas de SMTP Gmail, pas de mot de passe application)

Ce fichier assume que le `ZeebeClient` et le `ZeebeWorker` sont créés
au démarrage et passés à `register_tasks(worker, client)` depuis `main.py`.
Ne recréez PAS le channel ni le client à l'intérieur des tasks : cela provoque des erreurs d'authentification et de stabilité (403/forbidden).
"""

import os
import re
import json
import uuid
import requests
import mysql.connector
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from pyzeebe import Job

from pyzeebe import ZeebeWorker, ZeebeClient

WORKER_INSTANCE_ID = str(uuid.uuid4())[:8]
print(f"[WORKER STARTED] ID={WORKER_INSTANCE_ID} path={__file__}")


# ------------------------------------------------------------------
# Constantes
# ------------------------------------------------------------------
BANNED_WORDS = ["hate", "violence", "nsfw", "fake", "scam"]
BANNED_CATEGORIES = ["health", "finance"]
DEFAULT_TEMPLATE_ID = "d-4e0a7fa410dc4962895a8c909092bd50"


# ------------------------------------------------------------------
# Helper : envoi d'un e-mail via l'API SendGrid (template)
# ------------------------------------------------------------------
def send_sendgrid_template(to_email: str, to_name: str, template_id: str, data: Dict[str, Any]) -> None:
    print(f"[SENDGRID] Called from worker={WORKER_INSTANCE_ID}")
    api_key = os.getenv("SENDGRID_KEY")
    sender = os.getenv("EMAIL_SENDER")

    if not api_key:
        raise RuntimeError("SENDGRID_KEY is not set in environment")
    if not sender:
        raise RuntimeError("EMAIL_SENDER is not set in environment (must be a verified sender in SendGrid)")

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "from": {"email": sender, "name": "Automated system"},
        "personalizations": [{"to": [{"email": to_email, "name": to_name}], "dynamic_template_data": data}],
        "template_id": template_id,
    }

    resp = requests.post(url, headers=headers, json=body, timeout=10)
    print("[SendGrid] status:", resp.status_code)
    print("[SendGrid] body:", resp.text)
    resp.raise_for_status()
    print(f"✅ SendGrid template {template_id} sent to {to_email}")


# ------------------------------------------------------------------
# Register tasks
# ------------------------------------------------------------------
def register_tasks(worker: ZeebeWorker, client: ZeebeClient) -> None:
    print("[DEBUG] ZEEBE_CLIENT_ID present:", bool(os.getenv("ZEEBE_CLIENT_ID")))
    print("[DEBUG] ZEEBE_CLIENT_SECRET present:", bool(os.getenv("ZEEBE_CLIENT_SECRET")))
    print("[DEBUG] ZEEBE_ADDRESS present:", os.getenv("ZEEBE_ADDRESS"))


    @worker.task(task_type="check-eligibility")
    def check_eligibility(monthly_views: int, subscribers: int):
        eligibility_status = monthly_views >= 4000 and subscribers >= 1000
        print(f"Monthly views: {monthly_views}, Subscribers: {subscribers}, Eligible: {eligibility_status}")
        return {"eligibility_status": eligibility_status}


    @worker.task(task_type="verify-compliance")
    def verify_compliance(creator_name: str, channel_name: str, channel_description: str, channel_category: str):
        content = f"{creator_name} {channel_name} {channel_description}".lower()
        pattern = r"\b(" + "|".join(BANNED_WORDS) + r")\b"
        has_banned_word = bool(re.search(pattern, content))
        category_ok = channel_category.lower() not in BANNED_CATEGORIES
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
            return {"subject_status": "empty"}
        print("[Script Task] Subject valide. Envoi normal.")
        return {"subject_status": "ok"}


    @worker.task(task_type="check-AdSense")
    def checkAdSense_callDateWebAPI_createFile(job: Job):
        vars = job.variables
        full_name = vars.get("full_name")
        textfield_3f52r = vars.get("textfield_3f52r")
        number_8rp7aj = vars.get("number_8rp7aj")
        select_jepknc = vars.get("select_jepknc")
        card_number = vars.get("card_number")
        activate_checkbox = vars.get("activate_checkbox")

        print(f"[check-AdSense] Variables reçues : {vars}")

        # Vérification que toutes les variables existent
        if not all([full_name, textfield_3f52r, number_8rp7aj, select_jepknc, card_number, activate_checkbox]):
            print("❌ Certaines variables manquent dans le job")
            return {"adSense_status": False, "reason": "missing_fields"}

        print(f"Variables reçues : {full_name=}, {textfield_3f52r=}, {number_8rp7aj=}, {select_jepknc=}, {card_number=}, {activate_checkbox=}")

        # Vérification des champs
        def is_filled(value):
            return value is not None and str(value).strip() != ""

        if not all(map(is_filled, [full_name, textfield_3f52r, number_8rp7aj, card_number])):
            print("❌ Certains champs du formulaire sont vides.")
            return {"adSense_status": False, "reason": "missing_fields"}

        if not activate_checkbox:
            print("❌ La case 'Activate AdSense' n’est pas cochée.")
            return {"adSense_status": False, "reason": "checkbox_unchecked"}

        # Vérification DB
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "camunda_user"),
                password=os.getenv("DB_PASSWORD", "mdp_camunda"),
                database=os.getenv("DB_NAME", "BpmnDataBase"),
                connect_timeout=5,
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

        # Récupération de la date
        try:
            response = requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC", timeout=5)
            response.raise_for_status()
            current_date = response.json().get("datetime") or datetime.utcnow().isoformat()
        except Exception as e:
            print(f"⚠️ Impossible de récupérer la date via l'API, fallback à la date locale. Détail: {e}")
            current_date = datetime.utcnow().isoformat()

        # Création du fichier
        safe_date = current_date.replace(":", "-")
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
        return {"adSense_status": True, "date": datetime.utcnow().isoformat()}


    @worker.task(task_type="insert-into-db")
    def insert_into_db(full_name: str, textfield_3f52r: str, number_8rp7aj: int, select_jepknc: str, card_number: str):
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "camunda_user"),
                password=os.getenv("DB_PASSWORD", "mdp_camunda"),
                database=os.getenv("DB_NAME", "BpmnDataBase"),
                connect_timeout=5,
            )
            cursor = conn.cursor()
            sql = "INSERT INTO adsense_form (surname, firstname, age, language, iban_number) VALUES (%s, %s, %s, %s, %s)"
            values = (full_name, textfield_3f52r, number_8rp7aj, select_jepknc, card_number)
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Data inserted: {values}")
            return {"db_status": "success"}
        except mysql.connector.Error as err:
            print(f"❌ Database error: {err}")
            return {"db_status": "error", "error_msg": str(err)}


    @worker.task(task_type="submit_form")
    async def submit_form(formId: str = None, **form_data):
        formId = formId or str(uuid.uuid4())
        print(f"[submit_form] formId={formId} data={form_data}")
        try:
            await client.publish_message(
                name="form_submitted",
                correlation_key=formId,
                variables=form_data,
            )
            print("[submit_form] message publié → Pool2")
            return {"pool2_started": True, "formId": formId}
        except Exception as e:
            print(f"❌ Failed to publish 'form_submitted': {e}")
            raise


    # ------------------------------------------------------------------
    # VERSION CORRIGÉE DU WORKER notify_pool1
    # ------------------------------------------------------------------
    @worker.task(task_type="notify_pool1")
    async def notify_pool1(correlation_key: str = "fixed-key"):
        print(f"[notify_pool1] Publishing message with correlation key: {correlation_key}")
        await client.publish_message(
            name="Message_39eomtv",       # nom du message attendu par Pool1
            correlation_key=correlation_key,
            variables={}                   # envoyer variables si nécessaire
        )
        print("[notify_pool1] message publié → Pool1")
        return {"status": "ok"}


    @worker.task(task_type="send_pool2_form")
    async def send_pool2_form(
        full_name: str, textfield_3f52r: str, number_8rp7aj: int,
        select_jepknc: str, card_number: str, activate_checkbox: bool,
        formId: str = None,
    ):
        formId = formId or str(uuid.uuid4())
        print(f"[send_pool2_form] formId={formId}")
        print(f"  └─> {full_name=}, {textfield_3f52r=}, {number_8rp7aj=}, {select_jepknc=}, {card_number=}, {activate_checkbox=}")
        try:
            await client.publish_message(
            name="pool2_form_sent",
            correlation_key=formId,
            variables={
                "full_name": full_name,
                "textfield_3f52r": textfield_3f52r,
                "number_8rp7aj": number_8rp7aj,
                "select_jepknc": select_jepknc,
                "card_number": card_number,
                "activate_checkbox": activate_checkbox,
                "formId": formId,
            },
        )
            print("[send_pool2_form] message publié → Pool1")
            return {"message_sent": True, "formId": formId}
        except Exception as e:
            print(f"❌ Failed to publish pool2_form_sent: {e}")
            raise
