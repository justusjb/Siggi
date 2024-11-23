import uvicorn
from fastapi import FastAPI, Request
from twilio.twiml.voice_response import VoiceResponse, Gather
from typing import Dict, List
import os
from vertex_handler import VertexAIHandler

app = FastAPI()

# Initialize handlers
vertex_handler = VertexAIHandler()

# Conversations store
conversations: Dict[str, List[Dict[str, str]]] = {}

@app.get("/")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook/voice")
async def handle_call(request: Request):
    # Removed validation decorator
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    user_input = form_data.get("SpeechResult")

    print(f"Received call: {call_sid}, input: {user_input}")  # Debug logging

    response = VoiceResponse()

    if call_sid not in conversations:
        conversations[call_sid] = [
            {
                "role": "system",
                "content": "You are a helpful AI phone assistant. Keep responses brief and natural for voice conversation."
            }
        ]
        gather = Gather(
            input='speech',
            action='/webhook/voice',
            method='POST',
            language='en-US',
            speech_timeout='auto'
        )
        gather.say("Hello! How can I help you today?")
        response.append(gather)
        return str(response)

    if user_input:
        conversation = conversations[call_sid]
        conversation.append({"role": "user", "content": user_input})

        # Get AI response
        ai_response = await vertex_handler.get_response(conversation)
        conversation.append({"role": "assistant", "content": ai_response})

        gather = Gather(
            input='speech',
            action='/webhook/voice',
            method='POST',
            language='en-US',
            speech_timeout='auto'
        )
        gather.say(ai_response)
        response.append(gather)

    return str(response)

@app.post("/webhook/status")
async def call_status(request: Request):
    # Removed validation decorator
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")

    if call_status == "completed":
        conversations.pop(call_sid, None)

    return {"status": "success"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)