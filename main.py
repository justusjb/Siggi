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

        # First, say the greeting
        response.say("Hello! How can I help you today?")

        # Then set up the Gather
        gather = Gather(
            input='speech',
            action='/webhook/voice',
            method='POST',
            language='en-US',
            speech_timeout='auto',
            timeout=5
        )

        # Add a backup message in case speech isn't detected
        gather.say("Please speak after the tone.")

        response.append(gather)

        # Add a fallback if no input is received
        response.say("I didn't catch that. Please call again.")

        twiml = str(response)
        print(f"Sending TwiML response: {twiml}")  # Debug logging
        return twiml

    if user_input:
        conversation = conversations[call_sid]
        conversation.append({"role": "user", "content": user_input})

        # Get AI response
        ai_response = await vertex_handler.get_response(conversation)
        conversation.append({"role": "assistant", "content": ai_response})

        # First say the AI response
        response.say(ai_response)

        # Then set up the next Gather
        gather = Gather(
            input='speech',
            action='/webhook/voice',
            method='POST',
            language='en-US',
            speech_timeout='auto',
            timeout=5
        )

        gather.say("Please respond after the tone.")
        response.append(gather)

        # Add fallback
        response.say("I didn't catch that. Please call again.")

        twiml = str(response)
        print(f"Sending TwiML response: {twiml}")  # Debug logging
        return twiml

    return str(response)


@app.post("/webhook/status")
async def call_status(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    print(f"Call status update - SID: {call_sid}, Status: {call_status}")  # Debug logging

    if call_status == "completed":
        conversations.pop(call_sid, None)

    return {"status": "success"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)