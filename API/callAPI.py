import vertexai
import os
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

class VertexClient:
    def __init__(self, project_id, creds, model, region="us-central1"):
        vertexai.init(
            project=project_id,
            location=region,
            credentials=creds
        )
        self.model = GenerativeModel(model)

    def send_data_to_AI(self, prompt, temperature=0.5, top_p=0.8):
        # Config sinh nội dung
        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p
        )

        response = self.model.generate_content(
            prompt, generation_config=generation_config
        )
        return response.text