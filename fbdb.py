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
import datetime

cred = credentials.Certificate("serviceAccountKey.json")  
firebase_admin.initialize_app(cred)

db = firestore.client()


def save_chat(user_id, user_input, ai_response):
    chat_ref = db.collection("CHATS").document(user_id)

    new_messages = [
        {"role": "user", "text": user_input, "timestamp": datetime.datetime.now()},
        {"role": "ai", "text": ai_response, "timestamp": datetime.datetime.now()}
    ]

    chat_doc = chat_ref.get()
    
    if chat_doc.exists:
        existing_messages = chat_doc.to_dict().get("messages", [])
        updated_messages = existing_messages + new_messages  # Keep all messages
        chat_ref.set({"messages": updated_messages, "userId": user_id}, merge=True)
    else:
        chat_ref.set({"messages": new_messages, "userId": user_id})

def get_chat_history(user_id, limit=100):
    """Fetch the most recent chat messages for a user, up to the specified limit."""
    chat_ref = db.collection("CHATS").document(user_id)
    chat_doc = chat_ref.get()
    
    if not chat_doc.exists:
        return []
    
    messages = chat_doc.to_dict().get("messages", [])
    
    # Sort by timestamp if it exists
    if messages and "timestamp" in messages[0]:
        messages.sort(key=lambda x: x.get("timestamp"))
    
    # Return only the most recent messages up to the limit
    return messages[-limit:] if len(messages) > limit else messages

def ping_db():
    try:
        db.collection("chats").document("test_doc").set({"test": "Firestore connected!"})
        print("✅ Firestore connection successful!")
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")

