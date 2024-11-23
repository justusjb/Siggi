from vertexai import generative_models
from vertexai.preview.generative_models import GenerativeModel
import vertexai


class VertexAIHandler:
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        # If project_id is None, it will automatically detect from environment
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-pro")

    async def get_response(self, messages: List[Dict[str, str]]) -> str:
        chat = self.model.start_chat()

        # Add conversation history
        for message in messages[:-1]:  # All messages except the last one
            if message["role"] != "system":  # Skip system messages
                chat.send_message(message["content"])

        # Send the final message and get response
        response = chat.send_message(
            messages[-1]["content"],
            generation_config={
                "max_output_tokens": 1024,
                "temperature": 0.7,
            }
        )
        return response.text
