import uvicorn
from fastapi import FastAPI, Request, HTTPException
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator
from typing import Dict, List
import os
from vertex_handler import VertexAIHandler
from functools import wraps

app = FastAPI()

# Initialize handlers
vertex_handler = VertexAIHandler()
twilio_validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

# Conversations store
conversations: Dict[str, List[Dict[str, str]]] = {}


def validate_twilio_request(func):
    """Decorator to validate Twilio requests"""

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        form_data = await request.form()
        url = str(request.url)
        signature = request.headers.get("X-Twilio-Signature", "")

        # Convert form data to dict
        post_data = dict(form_data)

        # Validate the request
        if not twilio_validator.validate(url, post_data, signature):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

        return await func(request, *args, **kwargs)

    return wrapper


@app.get("/")
async def health_check():
    return {"status": "healthy"}


@app.post("/webhook/voice")
@validate_twilio_request
async def handle_call(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    user_input = form_data.get("SpeechResult")

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
@validate_twilio_request
async def call_status(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")

    if call_status == "completed":
        conversations.pop(call_sid, None)

    return {"status": "success"}


if __name__ == "__main__":
    if not os.environ.get('TWILIO_AUTH_TOKEN'):
        print("Warning: TWILIO_AUTH_TOKEN not set")
    port = int(os.getenv("PORT", "8080"))
    print(f"Starting server on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
