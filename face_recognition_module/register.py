import numpy as np
import cv2
import face_recognition
import os
import pickle
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import shutil
import random
from dotenv import load_dotenv


ENCODING_DIR = r'C:\Users\tmakh\OneDrive\Desktop\Python_AI\python\smart_supermarket_project\encodings'
IMAGES_DIR = r'C:\Users\tmakh\OneDrive\Desktop\Python_AI\python\smart_supermarket_project\face_images'
FACE_MATCH_TOLERANCE = 0.5

os.makedirs(ENCODING_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

cred_path = os.environ.get("FIREBASE_CREDENTIAL_PATH")
if not cred_path:
    raise ValueError("FIREBASE_CRED_PATH not set in environment variables")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()


def generate_random_purchased_history(num_items=3):
    sample_items = [
        ("Milk", 2.5),
        ("Bread", 1.0),
        ("Chips", 1.25),
        ("Soda", 1.75),
        ("Eggs", 3.0),
        ("Cheese", 4.5),
        ("Apples", 2.0),
        ("Cereal", 3.25),
        ("Yogurt", 1.2),
        ("Chocolate", 0.99),
        ("Chicken Breast", 8.99),
        ("Bananas", 1.25),
        ("Rice", 2.99),
        ("Pasta", 1.50),
        ("Orange Juice", 3.25),
        ("Nuts", 4.99),
        ("Tomatoes", 2.50),
        ("Onions", 1.75),
        ("Potatoes", 2.99),
        ("Coffee", 5.99),
        ("Ice Cream", 4.50),
        ("Peanut Butter", 3.99),
        ("Carrots", 1.50),
        ("Kiwi", 0.85),
        ("Donuts", 5.99),
        ("Shrimp", 9.99),
        ("Vinegar", 1.75)
    ]

    history = []

    for _ in range(num_items):
        item, price = random.choice(sample_items)
        date = datetime.utcnow().date() - timedelta(days=random.randint(1, 7))

        history.append({
            "item": item,
            "price": round(price, 2),
            "time": date.isoformat()
        })
    return history


def is_duplicate_phone(phone):
    docs = db.collection('customers').where(
        'phone_number', "==", phone).stream()
    for doc in docs:
        print(
            f"This phone number is already registered as {doc.to_dict()['name']}")
        return True
    return False


def generate_customer_id():
    docs = db.collection('customers').get()
    existing_ids = []

    for doc in docs:
        doc_id = doc.id
        if doc_id.startswith("CUST"):
            try:
                number = int(doc_id[4:])
                existing_ids.append(number)
            except ValueError:
                continue
    if not existing_ids:
        return "CUST001"

    existing_ids.sort()
    next_id = 1
    for id_number in existing_ids:
        if id_number == next_id:
            next_id += 1
        else:
            break

    return f"CUST{next_id:03d}"


def is_duplicate_face(new_encodings):
    try:
        docs = db.collection('customers').stream()
        for doc in docs:
            data = doc.to_dict()
            encs = data.get('encodings')
            if not encs:
                continue
            num_values = len(encs)
            if num_values % 128 != 0:
                print("Encoding length not 128")
                continue
            num_faces = num_values // 128
            stored_encodings = [np.asarray(encs[i*128:(i+1)*128], dtype=np.float64)
                                for i in range(num_faces)]
            matches = face_recognition.compare_faces(
                stored_encodings, new_encodings, tolerance=FACE_MATCH_TOLERANCE)
            if True in matches:
                print(f"This face is already registered as {data['name']}")
                return True

        return False
    except Exception as e:
        print(f"Error checking duplicate face from firestore: {e}")
        return False


def is_duplicate_name(name):
    docs = db.collection('customers').where('name', "==", name).stream()
    for doc in docs:
        print(f"The name {name} is already registered.")
        return True
    return False


def register_customer(name, phone, dob=None, gender=None, progress_callback=None):
    file_path = None
    person_image_dir = None

    if is_duplicate_name(name):
        return False, f"The name {name} is already registered. Please use a unique name."

    if is_duplicate_phone(phone):

        return False, f"The phone number {phone} is already registered. Please use a different one."

    cap = cv2.VideoCapture(0)
    encodings = []
    sample_count = 0
    max_samples = 10

    lock_face = None
    person_image_dir = os.path.join(IMAGES_DIR, name)

    try:

        while sample_count < max_samples:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Failed to capture from the Camera")
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb)

            if face_locations:

                if lock_face is None:
                    areas = [(right-left)*(bottom-top)
                             for (top, right, bottom, left) in face_locations]

                    largest_index_face = areas.index(max(areas))
                    lock_face = face_locations[largest_index_face]

                    face_encoding = face_recognition.face_encodings(rgb, [lock_face])[
                        0]
                    if is_duplicate_face(face_encoding):
                        return False, f"Registration cancelled this face is already registered."

                    if not os.path.exists(person_image_dir):
                        os.makedirs(person_image_dir)

                else:
                    matching_face_found = False
                    for location in face_locations:
                        top, right, bottom, left = location
                        (locked_top, locked_right,
                         locked_bottom, locked_left) = lock_face

                        if (abs(top-locked_top) < 50 and abs(right-locked_right) < 50 and abs(bottom-locked_bottom) < 50 and abs(left-locked_left) < 50):
                            lock_face = location
                            matching_face_found = True
                            break
                    if not matching_face_found:
                        continue

                face_encoding = face_recognition.face_encodings(rgb, [lock_face])[
                    0]
                encodings.append(face_encoding)
                sample_count += 1
                if progress_callback is not None:
                    progress_callback(sample_count, max_samples)

                image_path = os.path.join(
                    person_image_dir, f"sample_{sample_count}.jpg")
                cv2.imwrite(image_path, frame)

                (top, right, bottom, left) = lock_face
                cv2.rectangle(frame, (left, top),
                              (right, bottom), (0, 255, 0), 2)

                cv2.putText(frame, "Locked Face", (left, top-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                cv2.putText(frame, f"Sample {sample_count}/{max_samples}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow("Register Customer", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return False, "Registration Cancelled by user."

        if len(encodings) == max_samples:
            if not os.path.exists(ENCODING_DIR):
                os.makedirs(ENCODING_DIR)
            customer_id = generate_customer_id()
            file_path = os.path.join(ENCODING_DIR, f"{customer_id}_{name}.pkl")

            with open(file_path, 'wb') as f:
                pickle.dump(encodings, f)

            flattened_encodings = [
                val for enc in encodings for val in enc.tolist()]

            purchase_history = generate_random_purchased_history(num_items=3)

            return True, {
                'message': "Customer registered successfully",
                'customer_id': customer_id,
                'encodings': encodings,
                'flattened_encodings': flattened_encodings,
                'purchase_history': purchase_history,
                'file_path': file_path,
                'person_image_dir': person_image_dir,
                'dob': dob,
                'gender': gender
            }

        else:
            return False, "Failed to capture enough samples"
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    customer_name = input("Enter customer name to register: ")
    customer_phone = input("Enter customer phone number: ")
    register_customer(customer_name, customer_phone)
