# import firebase_admin
# from firebase_admin import credentials, firestore
# import os
# import json

# # Read Firebase credentials from environment variable
# firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")

# if firebase_credentials:
#     cred_dict = json.loads(firebase_credentials)  # Convert JSON string to dictionary
#     cred = credentials.Certificate(cred_dict)  # Load credentials from dict
#     firebase_admin.initialize_app(cred)
#     db = firestore.client()
#     print("✅ Firestore initialized successfully!")
# else:
#     raise ValueError("❌ Firebase credentials not found! Set the FIREBASE_CREDENTIALS environment variable.")

# def save_chat(user_input, api_response):
#     db.collection("chats").add({
#         "user_input": user_input,
#         "api_response": api_response,
#         "timestamp": firestore.SERVER_TIMESTAMP,  
#         "image": "",
#         "speech_to_text": ""
#     })

# def ping_db():
#     try:
#         db.collection("chats").document("test_doc").set({"test": "Firestore connected!"})
#         print("✅ Firestore connection successful!")
#     except Exception as e:
#         print(f"❌ Firestore connection failed: {e}")



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
