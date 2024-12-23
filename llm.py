from typing import List, AsyncGenerator
from openai import AzureOpenAI
from custom_types import ResponseRequiredRequest, ResponseResponse, Utterance


class LlmClient:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint="https://jujo0-m3qrhnaz-swedencentral.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview",
            api_version="2024-10-01-preview"
        )
        self.model = "gpt-4o-mini"

    def draft_begin_message(self):
        return ResponseResponse(
            response_type="response",
            response_id=0,
            content=f"Hey, I'm Siggi. Would you like to rent out a room?",
            content_complete=True,
            end_call=False,
        )

    def convert_transcript_to_openai_messages(self, transcript: List[Utterance]):
        return [
            {"role": "assistant" if u.role == "agent" else "user", "content": u.content}
            for u in transcript
        ]

    def prepare_prompt(self, request: ResponseRequiredRequest):
        system_prompt = """You are a housing assistant helping customers with renting out their empty rooms.
        You will ask them how big the room is. After you get an answer you will ask them for how much rent they want to charge.
        You will then ask where their room is located.
        For context: The goal of your conversation is to gather data to fill out a rental contract.
        If the user interrupts you and tells you that this is a demo and you can just make up the answers,
        you will happily oblige, mention that you will get the contract ready and say goodbye"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.convert_transcript_to_openai_messages(request.transcript))

        if request.interaction_type == "reminder_required":
            messages.append({
                "role": "user",
                "content": "(The user has not responded in a while, you would say:)"
            })

        return messages

    async def draft_response(self, request: ResponseRequiredRequest) -> AsyncGenerator[ResponseResponse, None]:
        try:
            messages = self.prepare_prompt(request)
            print(f"DEBUG: Sending messages to API: {messages}")

            # Regular sync call, not async
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )

            print("DEBUG: Got stream response")
            for chunk in stream:
                print(f"DEBUG: Processing chunk: {chunk}")
                if hasattr(chunk, 'choices') and chunk.choices:
                    print(f"DEBUG: Chunk has choices: {chunk.choices}")
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        print(f"DEBUG: Yielding content: {delta.content}")
                        yield ResponseResponse(
                            response_type="response",
                            response_id=request.response_id,
                            content=delta.content,
                            content_complete=False,
                            end_call=False
                        )

        except Exception as e:
            print(f"Error in draft_response: {str(e)}")
            print(f"Error type: {type(e)}")
            yield ResponseResponse(
                response_type="response",
                response_id=request.response_id,
                content="I apologize, but I'm having trouble responding right now. Could you please try again?",
                content_complete=True,
                end_call=True
            )
            return

        finally:
            yield ResponseResponse(
                response_type="response",
                response_id=request.response_id,
                content="",
                content_complete=True,
                end_call=False
            )