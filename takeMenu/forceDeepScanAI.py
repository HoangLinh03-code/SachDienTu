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

    # --- PROMPT ĐẶC BIỆT: DEEP SCAN - QUÉT MỤC LỤC CỰC CHI TIẾT ---
    prompt = """
    Bạn là chuyên gia số hóa sách chuyên khảo/học thuật. Nhiệm vụ: Trích xuất MỤC LỤC từ file PDF với ĐỘ CHI TIẾT CAO NHẤT.

    BƯỚC 1 - TÌM MỤC LỤC:
    - Mục lục có thể nằm ở ĐẦU hoặc CUỐI file PDF. Hãy quét toàn bộ file để tìm trang "MỤC LỤC".
    - Ưu tiên đọc từ trang mục lục chính thức của sách (có tiêu đề "MỤC LỤC" hoặc "NỘI DUNG").

    BƯỚC 2 - TRÍCH XUẤT TẤT CẢ CÁC CẤP:
    Sách học thuật thường có cấu trúc phân cấp sâu. Bạn PHẢI trích xuất TẤT CẢ các cấp mục lục, bao gồm:
    - Cấp 1 (ROOT): Tên tập/quyển (VD: "Tập 2")
    - Cấp 2 (CHƯƠNG): Chương I, Chương II, Phần I, Phụ lục,...
    - Cấp 3 (MỤC LỚN): I, II, III, IV,...
    - Cấp 4 (MỤC NHỎ): 1, 2, 3, 4,... hoặc a, b, c,...
    - Cấp 5+ nếu có: a), b), c),... hoặc các tiểu mục nhỏ hơn

    QUY TẮC BẮT BUỘC:
    1. PHẢI lấy đến MỤC NHỎ NHẤT có trong mục lục. Nếu trong mục lục có mục "1. Tên mục", "2. Tên mục" bên trong mục "I. Tên mục lớn" thì PHẢI tạo Content lồng nhau.
    2. Chỉ mục LÁ (mục nhỏ nhất, không có con) mới có "St" và "End". Các mục CHA chỉ có "Name", "Lid", "Content".
    3. Lid là số liên tục trong cùng một cấp Content, bắt đầu từ "1".
    4. Giữ nguyên tên mục như trong sách, KHÔNG sửa đổi hay viết tắt.
    5. Chỉ trả về JSON thuần túy, KHÔNG có markdown, KHÔNG giải thích.

    MẪU JSON MONG MUỐN (chú ý cấu trúc lồng nhau nhiều cấp):
    ```json
    [
        {
            "Name": "Tập 2",
            "Lid": "1",
            "Content": [
                {
                    "Name": "Chương I: TIÊU ĐỀ CHƯƠNG",
                    "Lid": "1",
                    "Content": [
                        {
                            "Name": "I. Tiêu đề mục lớn",
                            "Lid": "1",
                            "Content": [
                                { "Name": "1. Tiểu mục nhỏ nhất A", "Lid": "1", "St": "19", "End": "22" },
                                { "Name": "2. Tiểu mục nhỏ nhất B", "Lid": "2", "St": "23", "End": "25" }
                            ]
                        },
                        {
                            "Name": "II. Tiêu đề mục lớn khác",
                            "Lid": "2",
                            "Content": [
                                { "Name": "1. Tiểu mục C", "Lid": "1", "St": "26", "End": "30" },
                                { "Name": "2. Tiểu mục D", "Lid": "2", "St": "31", "End": "35" },
                                { "Name": "3. Tiểu mục E", "Lid": "3", "St": "36", "End": "40" }
                            ]
                        }
                    ]
                },
                {
                    "Name": "Chương II: TIÊU ĐỀ CHƯƠNG KHÁC",
                    "Lid": "2",
                    "Content": [
                        {
                            "Name": "I. Mục lớn",
                            "Lid": "1",
                            "St": "41",
                            "End": "50"
                        }
                    ]
                }
            ]
        }
    ]
    ```

    LƯU Ý QUAN TRỌNG:
    - Nếu một mục I, II, III KHÔNG có tiểu mục con (1, 2, 3) trong mục lục thì nó là mục LÁ → có "St", "End", KHÔNG có "Content".
    - Nếu một mục I, II, III CÓ tiểu mục con (1, 2, 3) trong mục lục thì nó là mục CHA → có "Content", KHÔNG có "St", "End".
    - Số trang "St" và "End" phải được lấy CHÍNH XÁC theo số ghi trong mục lục.
    - "End" của mục trước = "St" của mục sau - 1 (trừ khi mục lục ghi rõ số trang kết thúc).
    - Nếu mục lục chỉ ghi số trang bắt đầu, thì "End" = "St" của mục kế tiếp - 1.

    Hãy phân tích toàn bộ file PDF, tìm trang mục lục, và trả về JSON hoàn chỉnh với ĐỘ SÂU TỐI ĐA. Chỉ trả về JSON.
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
            print(f"✅ Đã tạo file JSON deep scan: {output_path}")
        else:
            print("❌ AI không trả về đúng định dạng JSON. Nội dung nhận được:\n", response_text)

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    # --- ĐIỀN ĐƯỜNG DẪN FILE PDF CỦA BẠN VÀO ĐÂY ---
    pdf_path = r"D:\CheckTool\SachDienTu\Lịch sử Việt Nam tập 02 Từ thế kỷ X đến thế kỷ XIV-Trần Thị Vinh-2014_compressed.pdf"
    
    if os.path.exists(pdf_path):
        file_name = os.path.splitext(os.path.basename(pdf_path))[0]
        extract_strict_structure(file_name, pdf_path)
    else:
        print(f"❌ Không tìm thấy file: {pdf_path}")