import uvicorn
from fastapi import FastAPI, Request
from twilio.twiml.voice_response import VoiceResponse, Gather
from typing import Dict, List
import httpx
import os
from pydantic import BaseModel

app = FastAPI()


class Message(BaseModel):
    role: str
    content: str


# Get environment variables (set these in Heroku config vars)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

# Simple in-memory store (switch to Redis/Database for production)
conversations: Dict[str, List[Message]] = {}


async def get_llm_response(messages: List[Message]) -> str:
    """Call Anthropic's Claude API"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json={
                    "model": MODEL,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        return "I apologize, but I'm having trouble processing your request right now."


@app.get("/")
async def health_check():
    """Endpoint for Heroku health checks"""
    return {"status": "healthy"}


@app.post("/webhook/voice")
async def handle_call(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    user_input = form_data.get("SpeechResult")

    response = VoiceResponse()

    # New call initialization
    if call_sid not in conversations:
        conversations[call_sid] = [
            Message(
                role="system",
                content="You are a helpful AI phone assistant. Keep responses brief and natural for voice conversation."
            )
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

    # Process user input
    if user_input:
        conversation = conversations[call_sid]
        conversation.append(Message(role="user", content=user_input))

        # Get AI response
        ai_response = await get_llm_response(conversation)
        conversation.append(Message(role="assistant", content=ai_response))

        # Continue conversation
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
    """Handle call status updates and cleanup"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")

    if call_status == "completed":
        conversations.pop(call_sid, None)

    return {"status": "success"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
