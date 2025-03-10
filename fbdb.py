import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")  
firebase_admin.initialize_app(cred)

db = firestore.client()

def save_chat(user_input, api_response):
    db.collection("chats").add({
        "user_input": user_input,
        "api_response": api_response,
        "timestamp": firestore.SERVER_TIMESTAMP,  
        "image": "",
        "speech_to_text": ""
    })

def ping_db():
    try:
        db.collection("chats").document("test_doc").set({"test": "Firestore connected!"})
        print("✅ Firestore connection successful!")
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")