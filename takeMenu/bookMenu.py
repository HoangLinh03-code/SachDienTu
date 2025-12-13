import json
import os
import sys

# --- BẮT ĐẦU ĐOẠN MÃ THÊM MỚI ---
# Lấy đường dẫn của thư mục hiện tại (thư mục takeMenu)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Tìm đường dẫn đến thư mục API (nằm ngang hàng với thư mục takeMenu)
api_dir = os.path.join(current_dir, '..', 'API')
# Thêm thư mục API vào danh sách đường dẫn tìm kiếm module của Python
sys.path.append(api_dir)
from callAPIforPDF import VertexClient
from google.oauth2 import service_account
from dotenv import load_dotenv

env_path = os.path.join(api_dir, '.env')

# Load file .env từ đúng đường dẫn đó
load_dotenv(env_path)

def getBookMenuFromAI(file_name, pdf_path, model="gemini-2.5-pro"):
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
        model=model
    )

    prompt = """
    Bạn là một hệ thống phân tích sách giáo khoa.
    Hãy đọc file PDF và trích xuất mục lục dưới dạng JSON với cấu trúc sau:
    ```
    [
        {
            "Name" : "<Tên chủ đề>",
            "Lid" : "<Mã chủ đề>",
            "Content" : [
                {
                    "Name" : "<Tên bài>",
                    "Lid" : "<Mã bài>",
                    "St" : "<Trang bắt đầu>",
                    "End" : "<Trang kết thúc>"
                }
            ]
        }
    ]
    ```
    Yêu cầu:
    - Chỉ đọc và tạo CHÍNH XÁC những nội dung có trong mục lục, TUYỆT ĐỐI KHÔNG thêm bất cứ nội dung nào mục lục không đề cập. Phần tử cấp độ nhỏ nhất là bài học có cấu trúc:
        {
            "Name" : "<Tên bài>",
            "Lid" : "<Mã bài>",
            "St" : "<Trang bắt đầu>",
            "End" : "<Trang kết thúc>"
        }
    - Chỉ tạo các phần tử "BÀI HỌC".
    - Trong "Lid" TUYỆT ĐỐI KHÔNG SỬ DỤNG kí tự đặc biệt như dấu chấm (.), dấu gạch ngang (-), dấu cách, chữ cái, chữ La Mã,... Chỉ sử dụng số.
    - Loại bỏ các mục không phải bài học như Lời nói đầu, Lời giới thiệu, Phụ lục, Tài liệu tham khảo, Chỉ mục,...
    - "Lid" là một số duy nhất.
    - Các mã bắt đầu từ 1, tạo mới khi bắt đầu những "Content" mới trong mỗi loại. Các mã cùng cấp phải liên tục.
    - Giữ nguyên tên như trong sách.
    - Trả về đầy đủ kết quả.
    - Trả về JSON hợp lệ, không giải thích thêm.
    - TUYỆT ĐỐI KHÔNG thêm các phần không cần thiết như tên sách, "```json", "Tất nhiên rồi...",...
    """
    print(f"⏳ Đang xử lý: {file_name}")
    try:
        response_text = client.send_data_to_AI(
            prompt,
            file_paths=[pdf_path],
            temperature=0.2
        )

        try:
            book_menu = json.loads(response_text)
        except json.JSONDecodeError:
            try:
                start = min(
                    x for x in [response_text.find("{"), response_text.find("[")] if x != -1
                )
                end = max(
                    x for x in [response_text.rfind("}"), response_text.rfind("]")] if x != -1
                ) + 1
                book_menu = json.loads(response_text[start:end])
            except Exception as e:
                raise ValueError(f"Lỗi parse JSON từ AI: {e}\nNội dung: {response_text}")

        json_path = os.path.join(os.path.dirname(pdf_path), f"{file_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(book_menu, f, ensure_ascii=False, indent=4)
        print(f"✔ Đã lưu {json_path}")
    except Exception as e:
        print(f"❌ Lỗi xử lý {file_name}: {e}")

def scan_folder(folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, f)
                file_name = os.path.splitext(os.path.basename(pdf_path))[0]
                getBookMenuFromAI(file_name, pdf_path)

if __name__ == "__main__":
    folder_path = r"D:\\NguVan"
    scan_folder(folder_path)