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

---

## 🔧 Installation & Setup  

### 1. Clone the repository  
```bash
git clone https://github.com/yourusername/smart_supermarket_project.git
cd smart_supermarket_project
2. Create a virtual environment and activate it
bash
Copy code
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows
3. Install dependencies
bash
Copy code
pip install -r requirements.txt
4. Configure environment variables
Create a .env file in the project root and add:

ini
Copy code
FIREBASE_CREDENTIALS=path/to/firebase/credentials.json
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_whatsapp_number
GROQ_API_KEY=your_groq_api_key
5. Run the system
Register a new customer:

bash
Copy code
python registration_gui.py
Start face recognition system:

bash
Copy code
python recognition.py
Run dashboard:

bash
Copy code
flask run
📸 Demo
(Insert screenshots, GIFs, or video links here showing registration, recognition, and dashboard in action)

📌 Future Work
Mobile app integration.

Advanced recommendation engine.

Multi-camera support.

Enhanced dashboard analytics.

👨‍💻 Authors
Tony Makhoul – Computer Engineering Student, Lebanese International University

📧 Contact: tmakhoul2002@gmail.com
🔗 LinkedIn: linkedin.com/in/tony-makhoul-05b6b7243
🔗 GitHub: github.com/TonyMakhoul

yaml
Copy code

---
