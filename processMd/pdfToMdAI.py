import json
import os
from API.callAPIforPDF import VertexClient
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

def getBookMenuFromAI(file_name, pdf_path, output_folder, failed_log_path, model="gemini-2.5-pro"):
    # Load credentials từ file JSON service account
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
        service_account_data,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    project_id = os.getenv('PROJECT_ID')
    # Khởi tạo client
    client = VertexClient(
        project_id=project_id,
        creds=creds,
        model_name=model
    )

    prompt = """
    Bạn là một chuyên viên phân tích văn bản. 
    Nhiệm vụ của bạn là phân tích file pdf đính kèm và trả về nội dung dạng Markdown theo những yêu cầu sau:
    + Chỉ trả về nội dung văn bản.
    + Trả về phản hồi duy nhất là nội dung của file dạng markdown.
    """
    print(f"⏳ Đang xử lý: {file_name}")
    try:
        response_text = client.send_data_to_AI(
            prompt,
            file_paths=[pdf_path],
            temperature=0.2
        )

        # Tạo thư mục lưu kết quả nếu chưa tồn tại
        os.makedirs(output_folder, exist_ok=True)

        # Đường dẫn file Markdown
        md_path = os.path.join(output_folder, f"{file_name}.md")

        # Ghi kết quả vào file .md
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(response_text.strip())

        print(f"✔ Đã lưu Markdown: {md_path}")

    except Exception as e:
        print(f"❌ Lỗi xử lý {file_name}: {e}")
        # Ghi lại file lỗi
        with open(failed_log_path, "a", encoding="utf-8") as log:
            log.write(f"{file_name} - {pdf_path} - Lỗi: {e}\n")

def scan_folder(folder):
    failed_log_path = os.path.join(os.path.dirname(folder), "FailedFile.txt")
    # Xóa log cũ nếu có
    if os.path.exists(failed_log_path):
        os.remove(failed_log_path)

    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, f)
                file_name = os.path.splitext(os.path.basename(pdf_path))[0]

                # Lấy tên thư mục chứa file pdf, ví dụ: SDT_TOANTAP1_KNTT_C3
                parent_folder_name = os.path.basename(root)

                # Tạo đường dẫn thư mục đầu ra
                output_folder = os.path.join(
                    os.path.dirname(folder),  # thư mục cha của folder gốc
                    "SDT_Done",
                    parent_folder_name
                )

                getBookMenuFromAI(file_name, pdf_path, output_folder, failed_log_path)

if __name__ == "__main__":
    folder_path = r"D:\\pdf\\SDT_NGUVAN_KNTT_C12"
    scan_folder(folder_path)
