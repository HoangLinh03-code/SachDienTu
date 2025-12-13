import json
import os
import sys

# --- Cấu hình import thư viện ---
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.join(current_dir, '..', 'API')
sys.path.append(api_dir)

from callAPIforPDF import VertexClient
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load môi trường
env_path = os.path.join(api_dir, '.env')
load_dotenv(env_path)

def extract_strict_structure(file_name, pdf_path, model="gemini-2.5-pro"):
    # Cấu hình Vertex AI
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

    client = VertexClient(
        project_id=os.getenv('PROJECT_ID'),
        creds=creds,
        model_name=model
    )

    # --- PROMPT ĐẶC BIỆT: ONE-SHOT LEARNING ---
    # Ta cung cấp cho AI đúng cái mẫu nó cần trả về để nó không thể làm sai.
    prompt = """
    Bạn là chuyên gia số hóa sách giáo khoa. Nhiệm vụ: Trích xuất mục lục sách Ngữ Văn 6 Tập 1 từ file PDF.

    YÊU CẦU CẤU TRÚC JSON ĐẦU RA (BẮT BUỘC GIỐNG HỆT MẪU):
    File JSON phải có đúng 3 cấp độ:
    1. Cấp 1 (ROOT): Tên là "Tập 1".
    2. Cấp 2 (CHƯƠNG): Các bài lớn (Ví dụ: "BÀI 1: CÂU CHUYỆN VÀ ĐIỂM NHÌN...").
    3. Cấp 3 (BÀI HỌC): Các văn bản đọc hiểu và phần thực hành.

    QUY TẮC XỬ LÝ QUAN TRỌNG:
    - Bỏ qua các từ khóa nhóm như "ĐỌC", "VIẾT", "NÓI VÀ NGHE". Hãy lấy trực tiếp các mục con của chúng làm Bài học (Cấp 3).
    - Ví dụ: Trong mục ĐỌC có "Vợ nhặt", "Chí Phèo" -> Thì "Vợ nhặt", "Chí Phèo" là Cấp 3.
    - Phải có số trang (St, End) cho Cấp 3.

    MẪU JSON MONG MUỐN (Hãy làm theo đúng định dạng này cho toàn bộ sách):
    ```json
    [
        {
            "Name": "Tập 1",
            "Lid": "1",
            "Content": [
                {
                    "Name": "BÀI 1: CÂU CHUYỆN VÀ ĐIỂM NHÌN TRONG TRUYỆN KỂ",
                    "Lid": "1",
                    "Content": [
                        { "Name": "Vợ nhặt (Trích - Kim Lân)", "Lid": "1", "St": "10", "End": "22" },
                        { "Name": "Chí Phèo (Trích - Nam Cao)", "Lid": "2", "St": "23", "End": "35" },
                        { "Name": "Thực hành tiếng Việt: Đặc điểm cơ bản của ngôn ngữ nói...", "Lid": "3", "St": "36", "End": "38" },
                        { "Name": "Viết văn bản nghị luận về một tác phẩm truyện...", "Lid": "4", "St": "39", "End": "44" },
                        { "Name": "Thuyết trình về nghệ thuật kể chuyện...", "Lid": "5", "St": "45", "End": "47" },
                        { "Name": "Củng cố, mở rộng", "Lid": "6", "St": "48", "End": "48" },
                        { "Name": "Thực hành đọc: Cải ơi! (Nguyễn Ngọc Tư)", "Lid": "7", "St": "48", "End": "53" }
                    ]
                },
                {
                    "Name": "BÀI 2: CẤU TỨ VÀ HÌNH ẢNH TRONG THƠ TRỮ TÌNH",
                    "Lid": "2",
                    "Content": [
                        { "Name": "Nhớ đồng (Tố Hữu)", "Lid": "1", "St": "56", "End": "58" },
                        { "Name": "Tràng giang (Huy Cận)", "Lid": "2", "St": "59", "End": "60" }
                        // ... Tiếp tục các bài tiếp theo tương tự ...
                    ]
                }
                // ... Làm tiếp cho đến hết BÀI 5 và ÔN TẬP HỌC KÌ 1 ...
            ]
        }
    ]
    ```

    Hãy phân tích toàn bộ file PDF và trả về JSON hoàn chỉnh theo mẫu trên. Chỉ trả về JSON, không giải thích.
    """

    print(f"🚀 Đang xử lý chính xác cấu trúc cho: {file_name}...")
    try:
        # Tăng token giới hạn để output không bị cắt giữa chừng vì JSON dài
        response_text = client.send_data_to_AI(
            prompt,
            file_paths=[pdf_path],
            temperature=0.0  # Nhiệt độ = 0 để đảm bảo chính xác tuyệt đối theo mẫu
        )

        # Lọc lấy phần JSON
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        if start != -1 and end != -1:
            json_content = response_text[start:end]
            final_data = json.loads(json_content)
            
            # Lưu file
            output_path = os.path.join(os.path.dirname(pdf_path), f"{file_name}.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            print(f"✅ Đã tạo file JSON chuẩn cấu trúc Tập 2: {output_path}")
        else:
            print("❌ AI không trả về đúng định dạng JSON. Nội dung nhận được:\n", response_text)

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    # --- ĐIỀN ĐƯỜNG DẪN FILE PDF CỦA BẠN VÀO ĐÂY ---
    pdf_path = r"d:\NguVan\C6_input\SHS Ngu van 6 tap 1 CTST (Ruot ITB 6.2.25).pdf"
    
    if os.path.exists(pdf_path):
        file_name = os.path.splitext(os.path.basename(pdf_path))[0]
        extract_strict_structure(file_name, pdf_path)
    else:
        print(f"❌ Không tìm thấy file: {pdf_path}")