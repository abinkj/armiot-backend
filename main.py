from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import openai
import fbdb
import assemblyai as aai
from dotenv import load_dotenv
import tempfile

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
ASSEMBLY_API_KEY = os.getenv("ASSEMBLY_API_KEY")
GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
GOOGLE_GEMINI_FLASH_2_0 = os.getenv("GOOGLE_GEMINI_FLASH_2_0")
# modal google/gemini-flash-1.5-8b-exp

# Create FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from your React Native app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to only allow your app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check database connection
fbdb.ping_db()

# Initialize OpenAI client
client = openai.OpenAI(
    api_key=GOOGLE_GEMINI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Initialize AssemblyAI
aai.settings.api_key = ASSEMBLY_API_KEY
transcriber = aai.Transcriber()


# Request Model
class ChatRequest(BaseModel):
    user_input: str
    user_id: str

@app.post("/chat")
async def chat_response(request: ChatRequest):
    try:
        user_input = request.user_input
        user_id = request.user_id  

        print(f"Processing request for user_id: {user_id}")
        
        try:
            chat_history = fbdb.get_chat_history(user_id, limit=100)
            print(f"Successfully retrieved chat history with {len(chat_history)} messages")
        except Exception as e:
            print(f"Error retrieving chat history: {str(e)}")
            chat_history = []  # Fallback to empty history
        
        # Convert chat history to OpenAI format
        try:
            openai_messages = [
                {"role": "assistant" if msg["role"] == "ai" else "user", "content": [{"type": "text", "text": msg["text"]}]}
                for msg in chat_history
            ]
            print(f"Converted {len(openai_messages)} messages to OpenAI format")
        except Exception as e:
            print(f"Error converting chat history: {str(e)}")
            openai_messages = []  # Fallback to empty messages
        
        # Add user message
        openai_messages.append({
            "role": "user",
            "content": [{"type": "text", "text": user_input}]
        })
        
        # Get AI response from OpenAI API
        try:
            print(f"Sending request to OpenAI with {len(openai_messages)} messages")
            completion = client.chat.completions.create(
                model="google/gemini-2.5-pro-exp-03-25:free",
                messages=openai_messages
            )
            api_response = completion.choices[0].message.content
            print(f"Successfully received response from OpenAI")
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            raise  # Re-raise to return error to client
        
        # Save chat to Firestore
        try:
            fbdb.save_chat(user_id, user_input, api_response)
            print(f"Successfully saved chat to Firestore")
        except Exception as e:
            print(f"Error saving chat to Firestore: {str(e)}")
            # Continue even if saving fails
        
        return {"response": api_response}
    
    except Exception as e:
        import traceback
        print("❌ ERROR in /chat endpoint:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    temp_file_path = None
    try:
        # Log received file information
        print(f"Received audio file: {audio_file.filename}, size: {audio_file.size} bytes")
        
        # Create a temporary file to save the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            # Write the uploaded file content to the temporary file
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        print(f"Saved audio to temporary file: {temp_file_path}")
        
        # Transcribe the audio using AssemblyAI
        transcript = transcriber.transcribe(temp_file_path)
        print(f"Transcription completed with status: {transcript.status}")
        print(transcript)
        
        # Log more details about the transcript object
        print(f"Transcript object properties: {dir(transcript)}")
        print(f"Transcript object representation: {repr(transcript)}")
        
        # Check for text in different possible attributes
        # transcript_text = ""
        transcript_text = ""
        if hasattr(transcript, 'text'):
            transcript_text = transcript.text
        elif hasattr(transcript, 'transcript'):
            transcript_text = transcript.transcript
        
        print(f"Final transcription text: '{transcript_text}'")
        
        
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            temp_file_path = None
        
        # Return whatever text we found (might be empty)
        return {"transcription": transcript_text}
            
    except Exception as e:
        # Ensure temporary file is deleted in case of error
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        print(f"Error in /transcribe endpoint: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        raise HTTPException(status_code=500, detail=str(e))
    temp_file_path = None
    try:
        # Log received file information
        print(f"Received audio file: {audio_file.filename}, size: {audio_file.size} bytes")
        
        # Create a temporary file to save the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            # Write the uploaded file content to the temporary file
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        print(f"Saved audio to temporary file: {temp_file_path}")
        
        # Transcribe the audio using AssemblyAI
        transcript = transcriber.transcribe(temp_file_path)
        print(f"Transcription completed with status: {transcript.status}")
        print(f"Transcription text: {transcript.text if hasattr(transcript, 'text') else 'No text attribute'}")
        
        
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            temp_file_path = None
        
        # If status is completed, we should have a successful transcription
        if transcript.status == aai.TranscriptStatus.completed:
            # Check if transcript has text
            if hasattr(transcript, 'text') and transcript.text:
                return {"transcription": transcript.text}
            else:
                print("Transcript status is completed but no text available")
                return {"transcription": ""}  # Return empty string instead of error
        else:
            error_msg = f"Transcription failed with status: {transcript.status}"
            print(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        # Ensure temporary file is deleted in case of error
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        print(f"Error in /transcribe endpoint: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        raise HTTPException(status_code=500, detail=str(e))
    temp_file_path = None
    try:
        # Log received file information
        print(f"Received audio file: {audio_file.filename}, size: {audio_file.size} bytes")
        
        # Create a temporary file to save the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            # Write the uploaded file content to the temporary file
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        print(f"Saved audio to temporary file: {temp_file_path}")
        
        # Transcribe the audio using AssemblyAI
        # This is where the issue is happening - let's fix the transcription call
        try:
            # Make sure you're using the API according to the latest SDK
            transcript = transcriber.transcribe(temp_file_path)
            print(f"Transcription completed with status: {transcript.status}")
            
            # Only proceed if we have a successful transcription
            if transcript.status == "completed" and transcript.text:
                # Clean up file first
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    temp_file_path = None
                
                return {"transcription": transcript.text}
            else:
                print(f"Transcription failed or empty: {transcript.status}")
                raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.status}")
                
        except Exception as transcription_error:
            print(f"Transcription API error: {str(transcription_error)}")
            raise HTTPException(status_code=500, detail=f"Transcription API error: {str(transcription_error)}")

    except Exception as e:
        # Ensure temporary file is deleted in case of error
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        print(f"Error in /transcribe endpoint: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        raise HTTPException(status_code=500, detail=str(e))
    temp_file_path = None
    try:
        # Log received file information
        print(f"Received audio file: {audio_file.filename}, size: {audio_file.size} bytes")
        
        # Rest of your code...
        
        # Log more details about the transcript
        print(f"Transcription status: {transcript.status}")
        print(f"Transcription result: {transcript.text if hasattr(transcript, 'text') else 'No text'}")
        
        # Check if transcription was successful
        if transcript.status == "completed":
            return {"transcription": transcript.text}
        else:
            error_msg = f"Transcription failed: {transcript.status}"
            print(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        # Log the detailed exception
        import traceback
        print(f"Exception in /transcribe endpoint: {str(e)}")
        print(traceback.format_exc())
        # Rest of your code...
        # Ensure temporary file is deleted in case of error
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"Error in /transcribe endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)




















# from fastapi import FastAPI, Query, HTTPException
# from pydantic import BaseModel
# import os
# import openai
# import fbdb
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# # Create FastAPI app
# app = FastAPI()

# # Check database connection
# fbdb.ping_db()

# # Initialize OpenAI client
# client = openai.OpenAI(
#     api_key=OPENAI_API_KEY,
#     base_url=OPENAI_BASE_URL
# )

# # Define request body model
# class ChatRequest(BaseModel):
#     user_input: str

# @app.post("/chat")  # Change from GET to POST
# async def chat_response(chat_request: ChatRequest):
#     try:
#         user_input = chat_request.user_input

#         # Make API request inside the endpoint
#         completion = client.chat.completions.create(
#             model="google/gemini-flash-1.5-8b-exp",
#             messages=[{"role": "user", "content": [{"type": "text", "text": user_input}]}]
#         )

#         # Extract response
#         api_response = completion.choices[0].message.content
#         print("Chatbot Response:", api_response)

#         # Save chat to database
#         fbdb.save_chat(user_input, api_response)

#         return {"response": api_response}
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # Run the FastAPI server
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


# from fastapi import FastAPI, Query
# import os
# import google.generativeai as genai
# import fbdb
# from dotenv import load_dotenv

# load_dotenv()
# GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")

# app = FastAPI()

# fbdb.ping_db()

# genai.configure(api_key=GEMINI_API_KEY)

# @app.get("/chat")
# async def chat_response(user_input: str = Query(..., description="User input for chatbot")):
#     try:
#         model = genai.GenerativeModel("gemini-2.0-flash")

#         response = model.generate_content(user_input)
        
#         api_response = response.text
#         print("Chatbot Response:", api_response)

#         fbdb.save_chat(user_input, api_response)

#         return {"response": api_response}

#     except Exception as e:
#         return {"error": str(e)}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
