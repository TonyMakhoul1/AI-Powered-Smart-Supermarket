# 🛒 AI-Powered Smart Supermarket  

## 📖 Overview  
The **AI-Powered Smart Supermarket** project is a real-time system designed to enhance customer experience using **face recognition, emotion detection, and cloud-based notifications**.  
It identifies returning customers, registers new ones, and sends **personalized WhatsApp messages**, all while maintaining a centralized database for analytics.  

---

## 🚀 Features  
- 👤 **Customer Registration**  
  - GUI-based registration with **Tkinter**.  
  - Capture customer face samples and generate **face encodings**.  
  - Store customer info in the Firebase Firestore database.  

- 🔍 **Face Recognition & Engagement**  
  - Detects customers in real time using a webcam.  
  - Updates customer’s **last visit** and **last detected emotion**.  
  - Uses **DeepFace** for emotion recognition.  

- 💬 **WhatsApp Notifications**  
  - Sends personalized messages using **Twilio API**.  
  - Welcomes new customers with a greeting message.  

- 📊 **Admin Dashboard**  
  - Flask-based dashboard for monitoring customer data.  
  - Filter by **gender, emotion, visit date, and age range**.  
  - Provides insights for customer engagement.  

---

## 🛠️ Tech Stack  
- **Python** – Flask, Tkinter, face_recognition, DeepFace, pyttsx3  
- **Firebase Firestore** – Cloud database  
- **Twilio API** – WhatsApp messaging  
- **HTML, CSS, Jinja2** – Dashboard UI  

---

## 📂 Project Structure  

AI-powered-smart-supermarket/
│
├── admin_dashboard/
│   ├── app.py                  # Flask app for the dashboard
│   ├── send_message.py         # WhatsApp messaging logic (dashboard-specific)
│   └── templates/
│       └── dashboard.html      # HTML template for the dashboard
│
├── face_recognition_module/
│   ├── recognition.py          # Real-time face recognition & engagement
│   ├── register.py             # Register new customers & capture face images
│   ├── registration_gui.py     # Tkinter-based GUI for registration
│   └── send_message.py         # WhatsApp messaging logic (general)

🔧 Installation & Setup

Clone the repository:

git clone https://github.com/yourusername/smart_supermarket_project.git
cd smart_supermarket_project


Create and activate a virtual environment.

Install dependencies:

pip install -r requirements.txt


Set up Firebase credentials and place them in the project root.

Add your Twilio SID/Auth Token and Groq API Key to .env.

▶️ Usage

Register a new customer:

python registration_gui.py


Run face recognition system:

python recognition.py


Start dashboard:

flask run

📸 Demo

(Screenshots or GIFs of registration, recognition, and dashboard here)

📌 Future Work

Mobile app integration.

Advanced recommendation engine.

Multi-camera support.

Enhanced dashboard analytics.

👨‍💻 Authors

Tony Makhoul – Computer Engineering Student, Lebanese International University
