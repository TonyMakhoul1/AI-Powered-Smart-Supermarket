import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
import datetime
import threading
from send_message import send_whatsapp_message
from deepface import DeepFace
import pytz
import pyttsx3
import time
from groq import Groq
import serial
from google.api_core.exceptions import ServiceUnavailable
import grpc
import os
from dotenv import load_dotenv


cred = os.getenv('FIREBASE_CREDENTIAL_PATH')
firebase_admin.initialize_app(cred)

db = firestore.client()


customers = db.collection("customers").stream()


groq_api_key = os.getenv('GROQ_API_KEY')
client = Groq(api_key=groq_api_key)

arduino_port = os.getenv('ARDUINO_PORT', 'COM3')
arduino = serial.Serial(arduino_port, 9600, timeout=1)
time.sleep(2)
THRESHOLD_DISTANCE = 100


def get_distance():
    try:
        line_bytes = arduino.readline()
        if line_bytes:
            line = line_bytes.decode('utf-8').strip()
            if line.startswith("distance:"):
                distance = float(line.split(":")[1])
                return distance
    except Exception as e:
        print("Error reading distance:", e)
    return None


def play_welcome_voice(message):
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)
    engine.say(message)
    engine.runAndWait()


def generate_voice_message(name, emotion):
    prompt = f"""
    Generate a short and friendly supermarket greeting.
    Customer name: {name}
    Detected emotion: {emotion}

    Rules:
    - Mention the name naturally.
    - Adapt tone to the emotion (e.g., if happy → cheerful, if sad → comforting).
    - Maximum 15 words.
    - Example: "Welcome back Tony! You look happy today, enjoy your shopping."
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )

    return chat_completion.choices[0].message.content


def generate_dynamic_message(name, emotion, purchase_history):
    if purchase_history:
        purchases_text = ", ".join(
            [f"{item['item']} at ${item['price']}" for item in purchase_history])
    else:
        purchases_text = "No previous purchases found"

    prompt = f"""
    Write a professional WhatsApp message for a customer in a supermarket.

    Customer name: {name}
    Emotion: {emotion}
    Purchase history: {purchases_text}

    Requirements:
    - Start with a warm welcome.
    - Recommend products and mention discounts naturally.
    - Adjust tone based on emotion (happy, sad, neutral, angry).
    - End with gratitude and brand name "Smart Supermarket".
    - Keep it friendly but professional.
    - IMPORTANT: The entire message must be under 1000 characters.
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )

    return chat_completion.choices[0].message.content


def detect_emotion(face_image):
    try:
        analysis = DeepFace.analyze(
            face_image, actions=['emotion'], enforce_detection=False)
        dominant_emotion = analysis[0]['dominant_emotion']
        return dominant_emotion
    except Exception as e:
        print(f"Emotion detection failed: {e}")
        return "Unknown"


def get_customer_doc(name, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return list(db.collection("customers")
                        .where('name', '==', name)
                        .stream())
        except (ServiceUnavailable, grpc.RpcError) as e:
            print(
                f"Firestore query failed for {name}, attempt {attempt+1}: {e}")
            time.sleep(delay)
    return None


print_visits = set()
print_emotions = {}
visit_lock = threading.Lock()


def update_last_visit(name, face_image, emotion):
    with visit_lock:
        customer_ref = get_customer_doc(name)
        if not customer_ref:
            print(
                f"Could not get customer {name} from Firestore after retries.")
            return

        for doc in customer_ref:

            data = doc.to_dict()
            phone = data.get("phone_number", None)
            last_visit = data.get("last_visit", None)
            purchase_history = data.get("purchase_history", [])
            now = datetime.datetime.utcnow()

            send_message = False

            if last_visit:
                last_visit_time = last_visit
                if last_visit_time.tzinfo is not None:
                    last_visit_time = last_visit_time.astimezone(
                        pytz.UTC).replace(tzinfo=None)

                time_diff = (now - last_visit_time).total_seconds()
                if time_diff >= 86400:
                    send_message = True
                else:
                    if name not in print_visits:
                        print(f"{name} already visited today.")
                        print_visits.add(name)

            else:
                send_message = True

            try:
                doc.reference.update(
                    {"last_visit": now, "last_emotion": emotion})
            except ServiceUnavailable:
                print(
                    f"Failed to update last_visit for {name} due to Firestore timeout.")

            if phone:
                if send_message and name not in print_visits:
                    try:
                        print_visits.add(name)
                        print_emotions[name] = emotion

                        voice_message = generate_voice_message(name, emotion)

                        threading.Thread(target=play_welcome_voice, args=(
                            voice_message,), daemon=True).start()

                        def delayed_message():
                            time.sleep(5)
                            message_body = generate_dynamic_message(
                                name, emotion, purchase_history)
                            send_whatsapp_message(phone, message_body)

                        threading.Thread(
                            target=delayed_message, daemon=True).start()

                    except Exception as e:
                        print("Twilio send failed: ", e)
            else:
                if name not in print_visits:
                    print(f"No phone number for {name}")
                    print_visits.add(name)

            break


known_encodings = []
known_names = []

for doc in customers:
    data = doc.to_dict()
    name = data['name']
    encodings = data['encodings']
    flat_encodings = np.array(encodings).reshape(-1, 128)

    for enc in flat_encodings:
        known_encodings.append(enc)
        known_names.append(name)
    print(f"{len(known_encodings)} encodings.")

cap = None

try:
    while True:
        distance = get_distance()
        if distance and distance < THRESHOLD_DISTANCE:
            if cap is None:
                cap = cv2.VideoCapture(0)
                print("Camera Opened")
            ret, frame = cap.read()
            if not ret:
                continue
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb)
            face_encodings = face_recognition.face_encodings(
                rgb, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(
                    known_encodings, face_encoding)
                face_distances = face_recognition.face_distance(
                    known_encodings, face_encoding)

                match_index = np.argmin(face_distances)
                name = "Unknown"

                top, right, bottom, left = face_location
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                face_image = frame[top:bottom, left:right]

                emotion = "Unknown"
                if matches[match_index]:
                    name = known_names[match_index]
                    emotion = detect_emotion(face_image)

                    threading.Thread(target=update_last_visit,
                                     args=(name, face_image, emotion)).start()

                if name == "Unknown":
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)

                cv2.rectangle(frame, (left, top),
                              (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                cv2.putText(frame, emotion, (left, top - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            cv2.imshow("Face Recognition", frame)

        else:
            if cap:
                cap.release()
                cap = None
                cv2.destroyAllWindows()
                print("Camera closed to save power!")

        if cv2.waitKey(1) == ord("q"):
            break


finally:
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    arduino.close()
    print("Program stopped safely")
