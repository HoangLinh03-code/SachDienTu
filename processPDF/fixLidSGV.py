import json
import os
from callAPIforPDF import VertexClient
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

def fixBookMenuFromAI(file_name, sbt_pdf_path, sgk_json_path, output_path, model="gemini-2.5-pro"):
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
    with open(sgk_json_path, "r", encoding="utf-8") as f:
        sgk_data = f.read()

    project_id = os.getenv('PROJECT_ID')
    # Khởi tạo client
    client = VertexClient(
        project_id=project_id,
        creds=creds,
        model=model
    )

    prompt = f"""
    Bạn là một hệ thống phân tích văn bản. Tôi có nội dung của file JSON như sau:
    ```
    {sgk_data}
    ```
    Nhiệm vụ của bạn là trả về số trang bắt đầu và trang kết thúc của từng bài học trong file JSON này, dựa trên mục lục của file PDF đính kèm.
    Hãy trả về nội dung JSON đã được sửa đổi, giữ nguyên cấu trúc ban đầu, chỉ thay đổi các trường Name, St, End cho phù hợp với mục lục của file pdf với thông tin sau:
        - Nếu tên bài học tại trường "Name" trong JSON trùng với tên bài học trong mục lục của file pdf, hãy giữ nguyên.
        - Nếu tên bài học không trùng, hãy bỏ qua bài học đó (không thêm vào JSON).
        - Nếu có bài học trong mục lục của file pdf không có trong JSON, hãy bỏ qua bài học đó (không thêm vào JSON).
        - Giữ nguyên trường "Lid" trong JSON.
        - Sửa lại trường "St" và "End" trong JSON cho đúng với trang bắt đầu và trang kết thúc của bài học trong mục lục của file pdf.
    Hãy chỉ trả về nội dung JSON đã được sửa đổi, không kèm theo bất kỳ chú thích hay giải thích nào khác.
    """

    response_text = client.send_data_to_AI(
        prompt,
        file_paths=[sbt_pdf_path],
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
        
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    json_path = os.path.join(output_path, f"{file_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(book_menu, f, ensure_ascii=False, indent=4)
    print(f"✔ Đã lưu {json_path}")

folder_path = r"C:\Users\Admin\Desktop\Maru\SachDienTu"
listL = ["SDT_TOAN"]
for item in listL:
    sbt_folder = os.path.join(folder_path, item, f"{item}_SGV")
    sgk_folder = os.path.join(folder_path, item, f"{item}_SGK đã fix")
    output_path = os.path.join(folder_path, item, f"{item}_SGV đã fix")
    if os.path.exists(sgk_folder):
        for root, dirs, files in os.walk(sbt_folder):
            for f in files:
                if f.lower().endswith(".pdf"):
                    sbt_json_path = os.path.join(root, f)
                    file_name = os.path.splitext(os.path.basename(f))[0]
                    print(f"Đang xử lý {file_name}...")
                    sgk_json_path = os.path.join(f"{sgk_folder}\{file_name}", f"{file_name}.json")
                    if os.path.exists(sgk_json_path):
                        fixBookMenuFromAI(file_name, sbt_json_path, sgk_json_path, output_path)