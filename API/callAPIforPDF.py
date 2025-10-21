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

    def send_data_to_AI(self, prompt, file_paths=None, temperature=0.5, top_p=0.8):
        parts = []

        # Nếu có nhiều file PDF
        if file_paths:
            for file_path in file_paths:
                with open(file_path, "rb") as f:
                    pdf_bytes = f.read()
                parts.append(
                    Part.from_data(data=pdf_bytes, mime_type="application/pdf")
                )

        # Thêm prompt dạng text
        parts.append(Part.from_text(prompt))

        # Config sinh nội dung
        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p
        )

        response = self.model.generate_content(
            parts, generation_config=generation_config
        )
        return response.text