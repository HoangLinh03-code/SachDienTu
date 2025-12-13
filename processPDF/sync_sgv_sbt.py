import json
import os
import sys

# --- 1. Cấu hình đường dẫn để import thư viện API ---
# Lấy đường dẫn thư mục hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))
# Trỏ ngược ra thư mục cha rồi vào thư mục API (giả sử cấu trúc: Project/processPDF/script.py và Project/API)
api_dir = os.path.join(current_dir, '..', 'API')
sys.path.append(api_dir)

from callAPIforPDF import VertexClient
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load key từ file .env
env_path = os.path.join(api_dir, '.env')
load_dotenv(env_path)

def sync_book_menu(sgk_json_path, target_pdf_path, output_suffix="_SGV"):
    """
    Hàm đồng bộ mục lục:
    - sgk_json_path: Đường dẫn file JSON chuẩn của SGK (đã làm ở Bước 1).
    - target_pdf_path: Đường dẫn file PDF của SGV hoặc SBT.
    - output_suffix: Đuôi tên file đầu ra (ví dụ: "_SGV" hoặc "_SBT").
    """
    
    # Kiểm tra file đầu vào
    if not os.path.exists(sgk_json_path):
        print(f"❌ Lỗi: Không tìm thấy file JSON SGK tại {sgk_json_path}")
        return
    if not os.path.exists(target_pdf_path):
        print(f"❌ Lỗi: Không tìm thấy file PDF tại {target_pdf_path}")
        return

    # Đọc nội dung JSON chuẩn của SGK
    with open(sgk_json_path, "r", encoding="utf-8") as f:
        sgk_content = f.read()

    # Cấu hình kết nối AI (Gemini)
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
        client = VertexClient(project_id=os.getenv('PROJECT_ID'), creds=creds, model_name="gemini-2.5-pro")
    except Exception as e:
        print(f"❌ Lỗi cấu hình API: {e}")
        return

    # Prompt gửi cho AI
    prompt = f"""
    Bạn là một trợ lý nhập liệu chính xác. 
    Tôi có file JSON Mục lục chuẩn của Sách Giáo Khoa (SGK) như sau:
    ```json
    {sgk_content}
    ```
    
    Nhiệm vụ của bạn là xem file PDF đính kèm (Đây là sách giáo viên hoặc sách bài tập tương ứng).
    Hãy trả về một file JSON **GIỮ NGUYÊN HOÀN TOÀN** cấu trúc (Name, Lid, Content) của SGK, nhưng thay đổi số trang (**St**, **End**) cho khớp với vị trí bài đó trong file PDF này.

    Quy tắc:
    1. **TUYỆT ĐỐI KHÔNG** thêm bài mới, không xóa bài cũ, không đổi ID (Lid). Cấu trúc cây phải y hệt mẫu.
    2. Chỉ tìm và sửa giá trị `St` (Start page) và `End` (End page).
    3. Nếu bài nào trong SGK không tìm thấy trong sách này (ví dụ SGV không có phần bài đọc), hãy để St="0", End="0".
    4. Trả về định dạng JSON hợp lệ.
    """

    print(f"⏳ Đang xử lý đồng bộ cho file: {os.path.basename(target_pdf_path)}...")
    
    try:
        # Gửi request lên AI
        response_text = client.send_data_to_AI(prompt, file_paths=[target_pdf_path], temperature=0.1)
        
        # Lọc lấy JSON từ phản hồi
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        if start != -1 and end != -1:
            json_str = response_text[start:end]
            new_menu = json.loads(json_str)
            
            # Tạo đường dẫn file output
            # Ví dụ: NguVan11.pdf -> NguVan11_SGV.json
            base_name = os.path.splitext(os.path.basename(target_pdf_path))[0]
            output_path = os.path.join(os.path.dirname(target_pdf_path), f"{base_name}{output_suffix}.json")
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(new_menu, f, ensure_ascii=False, indent=4)
            
            print(f"✅ Thành công! Đã tạo file: {output_path}")
        else:
            print(f"⚠️ AI trả về dữ liệu không đúng định dạng JSON. Nội dung:\n{response_text}")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    # ================= CẤU HÌNH CHẠY =================
    
    # 1. Đường dẫn đến file JSON SGK (File chuẩn đã làm ở Bước 1)
    path_sgk_json = r"d:\NguVan\C6_input\SHS Ngu van 6 tap 1 CTST (Ruot ITB 6.2.25).json"

    # 2. Đường dẫn đến file PDF Sách Giáo Viên (SGV)
    # Nếu chưa có file này, bạn cần tải về và để vào thư mục
    path_sgv_pdf = r"d:\NguVan\C6_input\SGV ngu van 6 tap 1 CTST (Ruot ITB 21.02.24).pdf" 
    
    # 3. Đường dẫn đến file PDF Sách Bài Tập (SBT)
    path_sbt_pdf = r"d:\NguVan\C6_input\SBT ngu van 6 tap 1 CTST (Ruot ITB 28.2.25).pdf"

    # ================= THỰC THI =================
    
    # Chạy đồng bộ cho SGV (Nếu có file PDF)
    if os.path.exists(path_sgv_pdf):
        sync_book_menu(path_sgk_json, path_sgv_pdf, output_suffix="_SGV")
    else:
        print(f"⚠️ Bỏ qua SGV: Không tìm thấy file {path_sgv_pdf}")

    # Chạy đồng bộ cho SBT (Nếu có file PDF)
    if os.path.exists(path_sbt_pdf):
        sync_book_menu(path_sgk_json, path_sbt_pdf, output_suffix="_SBT")
    else:
        print(f"⚠️ Bỏ qua SBT: Không tìm thấy file {path_sbt_pdf}")