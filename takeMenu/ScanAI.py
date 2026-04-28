import json
import os
import sys
import re

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


# ===========================================================================
# PROMPT DUY NHẤT — hoạt động với mọi loại sách giáo khoa
# Chiến lược 2 bước:
#   Bước 1 → Đọc trang MỤC LỤC / CONTENTS chính thức
#   Bước 2 → Quét TỪNG TRANG để tìm sub-section headings thực tế
#             (vì mục lục thường không liệt kê sub-sections)
# ===========================================================================
PROMPT = """
Bạn là chuyên gia số hóa sách giáo khoa. Nhiệm vụ: trích xuất CẤU TRÚC NỘI DUNG
ĐẦY ĐỦ từ file PDF với ĐỘ SÂU TỐI ĐA đến từng sub-section.

════════════════════════════════════════════════════════════
BƯỚC 1 — ĐỌC TRANG MỤC LỤC CHÍNH THỨC
════════════════════════════════════════════════════════════
Tìm trang có tiêu đề CONTENTS / MỤC LỤC / NỘI DUNG trong PDF.
Ghi nhận tên và số trang bắt đầu của từng Unit / Chương / Phần lớn.

════════════════════════════════════════════════════════════
BƯỚC 2 — QUÉT TỪNG TRANG ĐỂ TÌM SUB-SECTION HEADINGS
════════════════════════════════════════════════════════════
Mục lục chính thức THƯỜNG KHÔNG liệt kê sub-sections bên trong mỗi Unit/Chương.
Vì vậy bạn BẮT BUỘC phải đọc qua TỪNG TRANG nội dung của PDF để phát hiện
các heading sub-section xuất hiện trực tiếp trên trang.

Nhận diện heading sub-section dựa vào các dấu hiệu:
  - Font chữ to, in đậm, màu nổi bật (xanh, cam, đỏ...)
  - Có icon / mũi tên / số thứ tự đặc biệt đầu dòng
  - Nằm ở đầu một section mới, thường chiếm cả dòng riêng

Ví dụ sub-section thường gặp trong các loại sách:

  Sách Tiếng Anh (Global Success, Friends Plus...):
    Getting Started / A Closer Look 1 / A Closer Look 2
    Communication / Skills 1 / Skills 2 / Looking Back / Project
    Review X Language / Review X Skills

  Sách Toán / Khoa học tự nhiên:
    Bài X: <Tên bài> / I. / II. / III.
    Khám phá / Luyện tập / Vận dụng / Kết luận / Chú ý

  Sách Lịch sử / Địa lý / GDCD:
    Mục 1. / Mục 2. / Em có biết? / Ghi nhớ / Luyện tập

Với MỖI sub-section tìm được:
  - Ghi đúng TÊN như in trong sách (không viết tắt, không dịch)
  - St = số trang in ở góc trang nơi heading xuất hiện
  - End = St của sub-section kế tiếp - 1
  - Sub-section cuối của Unit → End = trang cuối của Unit đó

════════════════════════════════════════════════════════════
QUY TẮC JSON BẮT BUỘC
════════════════════════════════════════════════════════════
1. CẤU TRÚC PHÂN CẤP:
   ROOT  (tên sách / tên tập)          → CHA
     └── Unit / Chương / Phần lớn      → CHA
           └── Sub-section             → LÁ

2. Mục CHA: có "Content" (array), KHÔNG có "St" / "End".
   Mục LÁ : có "St" + "End" (string),  KHÔNG có "Content".

3. Các mục đặc biệt luôn là LÁ (không có Content):
   Book Map, Glossary, Lời nói đầu, Phụ lục, Bảng tra cứu...

4. "Lid": chuỗi số nguyên, đánh liên tục trong cùng một mảng,
   bắt đầu từ "1".

5. "St" và "End": chuỗi số nguyên tương ứng số trang IN trong sách,
   KHÔNG phải số thứ tự trang trong PDF viewer.

6. Chỉ trả về JSON thuần túy.
   KHÔNG markdown, KHÔNG giải thích, KHÔNG dấu ```json```.

════════════════════════════════════════════════════════════
MẪU JSON CHUẨN
════════════════════════════════════════════════════════════
[
  {
    "Name": "Tiếng Anh 6 - Tập Một",
    "Lid": "1",
    "Content": [
      { "Name": "Book Map", "Lid": "1", "St": "4", "End": "5" },
      {
        "Name": "UNIT 1: MY NEW SCHOOL",
        "Lid": "2",
        "Content": [
          { "Name": "Getting Started",       "Lid": "1", "St": "6",  "End": "7"  },
          { "Name": "A Closer Look 1",        "Lid": "2", "St": "8",  "End": "8"  },
          { "Name": "A Closer Look 2",        "Lid": "3", "St": "9",  "End": "10" },
          { "Name": "Communication",          "Lid": "4", "St": "11", "End": "11" },
          { "Name": "Skills 1",               "Lid": "5", "St": "12", "End": "12" },
          { "Name": "Skills 2",               "Lid": "6", "St": "13", "End": "13" },
          { "Name": "Looking Back & Project", "Lid": "7", "St": "14", "End": "15" }
        ]
      },
      {
        "Name": "Review 1",
        "Lid": "5",
        "Content": [
          { "Name": "Review 1 Language", "Lid": "1", "St": "36", "End": "36" },
          { "Name": "Review 1 Skills",   "Lid": "2", "St": "37", "End": "37" }
        ]
      },
      { "Name": "Glossary", "Lid": "10", "St": "70", "End": "71" }
    ]
  }
]

Hãy quét TOÀN BỘ PDF từ đầu đến cuối, phát hiện TẤT CẢ sub-section headings,
và trả về JSON hoàn chỉnh. CHỈ trả về JSON.
"""


# ===========================================================================
# HELPERS
# ===========================================================================

def _clean_json_response(text: str) -> str:
    """Loại bỏ markdown fences, cắt lấy đúng phần JSON array."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = text.find('[')
    end   = text.rfind(']') + 1
    if start == -1 or end == 0:
        return ""
    return text[start:end]


def _validate_structure(data: list, path: str = "root") -> list:
    """
    Kiểm tra đệ quy:
    - Mục CHA không được có St/End
    - Mục LÁ phải có cả St và End
    Trả về list cảnh báo (rỗng = hợp lệ).
    """
    warnings = []
    if not isinstance(data, list):
        return [f"{path}: phải là array"]

    for i, item in enumerate(data):
        loc         = f"{path}[{i}] '{item.get('Name', '?')}'"
        has_content = isinstance(item.get("Content"), list)
        has_st      = "St" in item
        has_end     = "End" in item

        if has_content and (has_st or has_end):
            warnings.append(f"⚠  {loc}: mục CHA không được có St/End")
        if not has_content and not (has_st and has_end):
            warnings.append(f"⚠  {loc}: mục LÁ thiếu St hoặc End")
        if has_content:
            warnings.extend(_validate_structure(item["Content"], loc))

    return warnings


def _count_nodes(data: list) -> tuple:
    """Đếm (số mục CHA, số mục LÁ) đệ quy."""
    parents, leaves = 0, 0
    for item in data:
        if isinstance(item.get("Content"), list):
            parents += 1
            p, l     = _count_nodes(item["Content"])
            parents += p
            leaves  += l
        else:
            leaves += 1
    return parents, leaves


# ===========================================================================
# HÀM CHÍNH
# ===========================================================================

def extract_strict_structure(
    file_name : str,
    pdf_path  : str,
    model     : str = "gemini-3.1-pro-preview",
):
    """
    Trích xuất cấu trúc phân cấp sâu từ PDF sách giáo khoa.

    Args:
        file_name : Tên file output (không có extension)
        pdf_path  : Đường dẫn tuyệt đối đến file PDF
        model     : Model Gemini sử dụng
    """
    # ── Khởi tạo Vertex AI ────────────────────────────────────────────────
    service_account_data = {
        "type":                        os.getenv("TYPE"),
        "project_id":                  os.getenv("PROJECT_ID"),
        "private_key_id":              os.getenv("PRIVATE_KEY_ID"),
        "private_key":                 os.getenv("PRIVATE_KEY", "").replace('\\n', '\n'),
        "client_email":                os.getenv("CLIENT_EMAIL"),
        "client_id":                   os.getenv("CLIENT_ID", ""),
        "auth_uri":                    os.getenv("AUTH_URI"),
        "token_uri":                   os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url":        os.getenv("CLIENT_X509_CERT_URL"),
        "universe_domain":             os.getenv("UNIVERSE_DOMAIN"),
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

    # ── Gọi AI ───────────────────────────────────────────────────────────
    print(f"\n🚀 Bắt đầu deep scan: {file_name}")
    print(f"   📄 PDF   : {pdf_path}")
    print(f"   🤖 Model : {model}")

    try:
        response_text = client.send_data_to_AI(
            PROMPT,
            file_paths=[pdf_path],
            temperature=0.0   # deterministic → chính xác nhất
        )
    except Exception as e:
        print(f"❌ Lỗi khi gọi AI: {e}")
        return

    # ── Parse JSON ────────────────────────────────────────────────────────
    json_str = _clean_json_response(response_text)
    if not json_str:
        print("❌ AI không trả về JSON hợp lệ.")
        print("📄 Raw response (500 ký tự đầu):", response_text[:500])
        return

    try:
        final_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print("📄 JSON string (500 ký tự đầu):", json_str[:500])
        return

    # ── Validate ─────────────────────────────────────────────────────────
    warnings = _validate_structure(final_data)
    if warnings:
        print(f"\n⚠  Có {len(warnings)} cảnh báo cấu trúc:")
        for w in warnings:
            print(f"   {w}")
    else:
        print("   ✅ Cấu trúc JSON hợp lệ.")

    # ── Lưu file ─────────────────────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(pdf_path), f"{file_name}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)

    parents, leaves = _count_nodes(final_data)
    print(f"\n✅ Đã lưu : {output_path}")
    print(f"   📊 Thống kê: {parents} mục CHA | {leaves} mục LÁ (có St/End)")


# ===========================================================================
# ENTRY POINT
# ===========================================================================
if __name__ == "__main__":

    # ── ĐIỀN ĐƯỜNG DẪN PDF VÀO ĐÂY ──────────────────────────────────────
    PDF_FILES = [
        r"D:\CheckTool\SachDienTu\Tiếng Anh 9\Tiếng Anh 9 Global Success_compress.pdf",
        # Thêm file khác nếu muốn xử lý hàng loạt:
        # r"D:\...\Toan_10_Tap1.pdf",
    ]

    for pdf_path in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f"❌ Không tìm thấy file: {pdf_path}")
            continue

        file_name = os.path.splitext(os.path.basename(pdf_path))[0]
        extract_strict_structure(file_name, pdf_path)