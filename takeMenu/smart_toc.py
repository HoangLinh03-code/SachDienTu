import json
import os
from PyPDF2 import PdfReader, PdfWriter
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
import vertexai
from dotenv import load_dotenv

# --- CẤU HÌNH ---
# Điền đường dẫn file 64MB của bạn vào đây
PDF_PATH_INPUT = r"d:\NguVan\C6_input\SHS Ngu van 6 tap 1 CTST (Ruot ITB 6.2.25).pdf"
MODEL_NAME = "gemini-2.5-pro" # Hoặc "gemini-2.5-pro" nếu bạn chắc chắn acc có quyền

# Load env
load_dotenv(r"D:\CheckTool\SachDienTu\API\.env") # Trỏ đúng file .env của bạn

def scan_toc_large_file(pdf_path):
    print(f"📦 File gốc nặng quá (64MB), đang cắt mục lục để xử lý...")
    
    # 1. Cắt file tạm
    temp_pdf = "temp_toc_c6.pdf"
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        # Lấy 20 trang đầu (thường mục lục nằm đây)
        for i in range(min(20, len(reader.pages))):
            writer.add_page(reader.pages[i])
        
        with open(temp_pdf, "wb") as f:
            writer.write(f)
        print(f"✂️ Đã cắt ra file tạm: {temp_pdf}")
    except Exception as e:
        print(f"❌ Lỗi cắt PDF: {e}")
        return

    # 2. Gửi file nhẹ lên AI
    try:
        # Setup AI (Copy từ code cũ của bạn)
        raw_key = os.getenv("PRIVATE_KEY", "").replace('\\n', '\n')
        creds = service_account.Credentials.from_service_account_info(
            {
                "type": os.getenv("TYPE"),
                "project_id": os.getenv("PROJECT_ID"),
                "private_key_id": os.getenv("PRIVATE_KEY_ID"),
                "private_key": raw_key,
                "client_email": os.getenv("CLIENT_EMAIL"),
                "client_id": os.getenv("CLIENT_ID"),
                "auth_uri": os.getenv("AUTH_URI"),
                "token_uri": os.getenv("TOKEN_URI"),
                "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
                "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
            },
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        vertexai.init(project=os.getenv("PROJECT_ID"), location="us-central1", credentials=creds)
        client = GenerativeModel(MODEL_NAME)

        prompt = """
        Bạn là chuyên gia cấu trúc dữ liệu sách giáo khoa.
        Nhiệm vụ: Trích xuất MỤC LỤC từ file PDF này sang JSON.

        1. QUY TẮC LOẠI TRỪ (QUAN TRỌNG):
           - TUYỆT ĐỐI KHÔNG đưa vào JSON các mục: "Lời nói đầu", "Hướng dẫn sử dụng", "Phần mở đầu", "Cấu trúc sách".
           - Bỏ qua toàn bộ các trang giới thiệu đầu sách.

        2. QUY TẮC ĐÁNH SỐ (Lid):
           - Bắt đầu tính Lid="1" từ "Bài mở đầu" (hoặc Bài 1 nếu không có bài mở đầu).
           - Cấu trúc cây phải bắt đầu ngay vào nội dung bài học chính.

        3. MẪU OUTPUT JSON 3 CẤP (BẮT BUỘC):
        [
          {
            "Name": "Tập 1",
            "Lid": "1",
            "Content": [
              {
                "Name": "Bài mở đầu: HOÀ NHẬP VÀO MÔI TRƯỜNG MỚI", 
                "Lid": "1", 
                "Content": [
                    { "Name": "Chia sẻ cảm nghĩ về môi trường...", "Lid": "1", "St": "9", "End": "9" },
                    { "Name": "Khám phá một chặng hành trình", "Lid": "2", "St": "10", "End": "11" }
                ]
              },
              {
                "Name": "Bài 1: LẮNG NGHE LỊCH SỬ NƯỚC MÌNH",
                "Lid": "2",
                "Content": [...]
              }
            ]
          }
        ]
        
        Lưu ý: 
        - Nếu gặp các mục con là "ĐỌC", "VIẾT", "NÓI VÀ NGHE", hãy lấy các bài nhỏ bên trong làm cấp con (như mẫu trên), không để tiêu đề "ĐỌC" đứng một mình làm mục lục nếu có thể.
        - Trả về JSON thuần túy, không Markdown.
        """

        print(f"⏳ Đang gửi lên AI...")
        with open(temp_pdf, "rb") as f:
            pdf_bytes = f.read()
        
        response = client.generate_content(
            [Part.from_data(data=pdf_bytes, mime_type="application/pdf"), prompt],
            generation_config=GenerationConfig(temperature=0.0)
        )
        
        # Lưu kết quả
        text = response.text
        start, end = text.find('['), text.rfind(']') + 1
        if start != -1:
            data = json.loads(text[start:end])
            if isinstance(data, list) and len(data) > 0:
                root = data[0]
                if "Content" in root:
                    # Lọc chỉ giữ lại các mục có từ khóa "Bài" hoặc "Chương"
                    filtered_content = []
                    new_lid = 1
                    for item in root["Content"]:
                        name_lower = item.get("Name", "").lower()
                        # Bỏ qua các từ khóa rác
                        if any(x in name_lower for x in ["lời nói đầu", "hướng dẫn", "phần mở đầu"]):
                            continue
                        
                        # Đánh lại số Lid
                        item["Lid"] = str(new_lid)
                        new_lid += 1
                        filtered_content.append(item)
                    
                    root["Content"] = filtered_content
            out_name = os.path.splitext(os.path.basename(pdf_path))[0] + ".json"
            out_path = os.path.join(os.path.dirname(pdf_path), out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"✅ XONG! Đã có file JSON: {out_path}")
        else:
            print("⚠️ AI không trả về JSON.")

    except Exception as e:
        print(f"❌ Lỗi AI: {e}")
    finally:
        if os.path.exists(temp_pdf): os.remove(temp_pdf)

if __name__ == "__main__":
    scan_toc_large_file(PDF_PATH_INPUT)