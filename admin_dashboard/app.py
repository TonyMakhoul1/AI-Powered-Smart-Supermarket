from flask import Flask, render_template, request, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, firestore
from send_message import send_whatsapp_message
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(BASE_DIR, '..', 'face_recognition_module',
                         'smart-supermarket-project-firebase-adminsdk-fbsvc-7e87b3b077.json')


if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()


@app.route("/")
def dashboard():
    if request.args.get("action") == "reset":
        return redirect(url_for("dashboard"))

    gender_filter = request.args.get("gender")
    emotion_filter = request.args.get("emotion")
    visit_date_filter = request.args.get("visit_date")

    customers_ref = db.collection("customers")
    docs = customers_ref.stream()

    customers = []
    total_customers = 0
    male_count = 0
    female_count = 0

    unique_gender = set()
    unique_emotions = set()

    age_min = request.args.get("age_min", type=int)
    age_max = request.args.get("age_max", type=int)

    for doc in docs:
        data = doc.to_dict()

        dob = data.get("date_of_birth")

        if dob:
            try:
                dob_date = datetime.strptime(dob, "%Y-%m-%d")
                age = (datetime.now().date() - dob_date.date()).days // 365
                data["age"] = age
            except Exception:
                data["age"] = None
        else:
            data["age"] = None

        if data.get("gender"):
            unique_gender.add(data["gender"])
        if data.get("last_emotion"):
            unique_emotions.add(data["last_emotion"])

        if gender_filter and data.get("gender") != gender_filter:
            continue
        if emotion_filter and data.get("last_emotion") != emotion_filter:
            continue
        if visit_date_filter and isinstance(data.get("last_visit"), datetime):
            visit_date = data["last_visit"].strftime("%Y-%m-%d")
            if visit_date != visit_date_filter:
                continue

        if age_min and (data.get("age") is None or data["age"] < age_min):
            continue

        if age_max and (data.get("age") is None or data["age"] > age_max):
            continue

        customers.append(data)

        total_customers += 1
        if data.get("gender") == "Male":
            male_count += 1
        elif data.get("gender") == "Female":
            female_count += 1

    stats = {
        "total": total_customers,
        "male": male_count,
        "female": female_count
    }

    return render_template("dashboard.html", customers=customers, stats=stats,
                           genders=sorted(unique_gender),
                           emotions=sorted(unique_emotions),
                           request=request)


@app.route("/send_messages", methods=["POST"])
def send_messages():
    action = request.form.get("action")
    message = request.form.get("message", "").strip()

    if not message:
        flash("Message cannot be empty!", "danger")
        return redirect(url_for("dashboard"))

    gender_filter = request.form.get("gender")
    emotion_filter = request.form.get("emotion")
    visit_date_filter = request.form.get("visit_date")
    age_min = request.form.get("age_min", type=int)
    age_max = request.form.get("age_max", type=int)

    has_filter = any([
        gender_filter,
        emotion_filter,
        visit_date_filter,
        age_min is not None,
        age_max is not None
    ])

    if action == "selected":
        selected_numbers = request.form.getlist("selected_customers")
        if not selected_numbers:
            flash("No customers selected", "warning")
            return redirect(url_for("dashboard"))

        for number in selected_numbers:
            send_whatsapp_message(number, message)

        flash(
            f"Message sent to {len(selected_numbers)} selected customers!", "success")

    elif action == "filtered":

        if not has_filter:
            flash("No filter is applied!", "warning")
            return redirect(url_for("dashboard"))

        customers_ref = db.collection("customers")
        docs = customers_ref.stream()

        count = 0
        for doc in docs:
            data = doc.to_dict()

            dob = data.get("date_of_birth")

            if dob:
                try:
                    dob_date = datetime.strptime(dob, "%Y-%m-%d")
                    age = (datetime.now().date() - dob_date.date()).days // 365
                    data["age"] = age
                except Exception:
                    data["age"] = None
            else:
                data["age"] = None

            if gender_filter and data.get("gender") != gender_filter:
                continue
            if emotion_filter and data.get("last_emotion") != emotion_filter:
                continue
            if visit_date_filter and isinstance(data.get("last_visit"), datetime):
                visit_date = data["last_visit"].strftime("%Y-%m-%d")
                if visit_date != visit_date_filter:
                    continue

            if age_min and (age is None or age < age_min):
                continue
            if age_max and (age is None or age > age_max):
                continue

            if data.get("phone_number"):
                send_whatsapp_message(data["phone_number"], message)
                count += 1

        flash(f"Message sent to {count} filtered customers!", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
