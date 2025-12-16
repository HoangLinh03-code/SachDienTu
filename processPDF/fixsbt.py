import json
import os
import sys

# --- Cấu hình đường dẫn thư viện API ---
# Giả sử bạn đang chạy file này ở thư mục D:\FixNV11
# Và thư mục API nằm ở đâu đó, bạn cần trỏ đúng. 
# Nếu không có thư mục API gốc, ta dùng lại class VertexClient khai báo trực tiếp dưới đây cho nhanh.

from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
from dotenv import load_dotenv

# --- KHAI BÁO LẠI CLASS API (Để chạy độc lập không cần import loằng ngoằng) ---
class VertexClient:
    def __init__(self, project_id, creds, model, region="us-central1"):
        vertexai.init(project=project_id, location=region, credentials=creds)
        self.model = GenerativeModel(model)

    def send_data_to_AI(self, prompt, file_paths=None, temperature=0.5, top_p=0.8):
        parts = []
        if file_paths:
            for file_path in file_paths:
                with open(file_path, "rb") as f:
                    pdf_bytes = f.read()
                parts.append(Part.from_data(data=pdf_bytes, mime_type="application/pdf"))
        parts.append(Part.from_text(prompt))
        generation_config = GenerationConfig(temperature=temperature, top_p=top_p)
        response = self.model.generate_content(parts, generation_config=generation_config)
        return response.text

# --- LOAD ENV ---
# Bạn nhớ tạo file .env chứa key ở cùng thư mục chạy code này hoặc điền cứng vào code nếu cần
load_dotenv(r'D:\\CheckTool\\SachDienTu\\API\\.env') 

def fixBookMenuFromAI(file_name, sbt_pdf_path, sgk_json_path, output_path, model="gemini-2.5-pro"):
    # Load credentials
    try:
        service_account_data = {
            "type": os.getenv("TYPE"),
            "project_id": os.getenv("PROJECT_ID"),
            "private_key_id": os.getenv("PRIVATE_KEY_ID"),
            "private_key": os.getenv("PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("CLIENT_EMAIL"),
            "client_id": os.getenv("CLIENT_ID", ""),
            "auth_uri": os.getenv("AUTH_URI"),
            "token_uri": os.getenv("TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("UNIVERSE_DOMAIN")
        }
        creds = service_account.Credentials.from_service_account_info(
            service_account_data, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    except:
        print("❌ Lỗi load key .env! Kiểm tra lại file .env")
        return

    project_id = os.getenv('PROJECT_ID')
    client = VertexClient(project_id=project_id, creds=creds, model=model)

    # Đọc file SGK làm chuẩn
    with open(sgk_json_path, "r", encoding="utf-8") as f:
        sgk_data = f.read()

    prompt = f"""
    Bạn là một hệ thống phân tích văn bản. Tôi có nội dung của file JSON SGK chuẩn như sau:
    ```
    {sgk_data}
    ```
    Nhiệm vụ của bạn là trả về số trang bắt đầu (St) và trang kết thúc (End) của từng bài học trong file JSON này, dựa trên mục lục của file PDF Sách Bài Tập (SBT) đính kèm.
    
    YÊU CẦU:
    1. Giữ nguyên cấu trúc JSON gốc (Lid, Name).
    2. Chỉ thay đổi "St" và "End" cho khớp với sách SBT.
    3. Nếu bài học trong SGK không có trong SBT, điền St="0", End="0".
    4. Trả về JSON thuần.
    """

    print(f"⏳ Đang chạy fixLidSBT cho: {file_name}...")
    try:
        response_text = client.send_data_to_AI(prompt, file_paths=[sbt_pdf_path], temperature=0.1)

        # Parse JSON
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        if start != -1:
            book_menu = json.loads(response_text[start:end])
            
            # Lưu file output
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            # Tên file output theo quy chuẩn dự án: TenFile_SBT.json
            json_out_path = os.path.join(output_path, f"{file_name}_SBT.json")
            with open(json_out_path, "w", encoding="utf-8") as f:
                json.dump(book_menu, f, ensure_ascii=False, indent=4)
            print(f"✔ Đã lưu file SBT JSON: {json_out_path}")
        else:
            print("❌ AI không trả về JSON hợp lệ.")
            
    except Exception as e:
        print(f"❌ Lỗi xử lý {file_name}: {e}")


if __name__ == "__main__":
    # --- CẤU HÌNH ĐƯỜNG DẪN CỦA BẠN ---
    working_dir = r"D:\NguVan\C6_input"
    
    # File PDF SBT
    sbt_pdf = os.path.join(working_dir, "SBT ngu van 6 tap 1 CTST (Ruot ITB 28.2.25).pdf")
    
    # File JSON SGK (Chuẩn)
    sgk_json = os.path.join(working_dir, "SHS Ngu van 6 tap 1 CTST (Ruot ITB 6.2.25).json")
    
    # Tên file (để đặt tên output)
    file_name = "SBT NGU VAN 6 TAP 1 CTST"
    
    # Thư mục xuất kết quả
    output_dir = working_dir 

    if os.path.exists(sbt_pdf) and os.path.exists(sgk_json):
        fixBookMenuFromAI(file_name, sbt_pdf, sgk_json, output_dir)
    else:
        print("❌ Thiếu file PDF hoặc JSON SGK đầu vào.")