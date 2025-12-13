import json
import os
import openpyxl
from PyPDF2 import PdfReader, PdfWriter

# ==============================================================================
# PHẦN 1: LOGIC TẠO ID & EXCEL (Dựa trên processPDF/lessonTree.py)
# ==============================================================================
def process_lesson_tree(pdf_path, json_path, output_folder):
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Tạo folder riêng cho từng sách trong KetQua
    book_output_dir = os.path.join(output_folder, file_name)
    if not os.path.exists(book_output_dir):
        os.makedirs(book_output_dir)

    print(f"🔹 Đang xử lý cây kiến thức cho: {file_name}...")

    with open(json_path, "r", encoding="utf-8") as f:
        bookDatas = json.load(f)

    # Tạo Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cay Kien Thuc"
    ws.append(["ID", "Tên Bài", "Trang Bắt Đầu", "Trang Kết Thúc"])

    lessons_flat_list = []

    # Hàm đệ quy duyệt cây và sinh ID (Logic của lessonTree.py)
    def traverse_tree(data, parent_id=""):
        for item in data:
            Lid = str(item.get("Lid", ""))
            # Tạo ID nối tiếp: cha_con (VD: 1_1_1)
            cur_id = f"{parent_id}_{Lid}" if parent_id else Lid
            Name = item.get("Name", "")
            
            # Kiểm tra xem đây có phải là bài học cuối cùng (có St, End) không
            st = str(item.get("St", "0"))
            end = str(item.get("End", "0"))
            
            # Ghi vào Excel
            ws.append([cur_id, Name, st, end])

            if "Content" in item and isinstance(item["Content"], list) and item["Content"]:
                # Nếu còn con thì duyệt tiếp
                traverse_tree(item["Content"], cur_id)
            else:
                # Nếu là nút lá (bài học), thêm vào danh sách để cắt
                if st != "0" and end != "0":
                    lessons_flat_list.append({
                        "Name": Name,
                        "Lid": cur_id, # ID đã được làm phẳng (VD: 1_1_1)
                        "St": st,
                        "End": end
                    })

    # Bắt đầu duyệt (Giả sử root là list hoặc dict)
    if isinstance(bookDatas, list):
        # Thông thường JSON của bạn có root là [ { "Name": "Tập 1"... } ]
        # Để ID đẹp (bắt đầu bằng 1_...), ta duyệt từng phần tử
        traverse_tree(bookDatas)
    elif isinstance(bookDatas, dict):
        traverse_tree([bookDatas])

    # Lưu Excel
    excel_path = os.path.join(book_output_dir, f"{file_name}.xlsx")
    wb.save(excel_path)
    print(f"   ✅ Đã tạo Excel: {excel_path}")

    # Lưu JSON phẳng (để dùng cho bước cắt)
    json_flat_path = os.path.join(book_output_dir, f"{file_name}_processed.json")
    with open(json_flat_path, "w", encoding="utf-8") as f:
        json.dump(lessons_flat_list, f, ensure_ascii=False, indent=4)
    
    return json_flat_path, book_output_dir

# ==============================================================================
# PHẦN 2: LOGIC CẮT PDF (Dựa trên CutPDF/cutTap.py)
# ==============================================================================
def cut_pdf_from_flat_json(pdf_path, json_flat_path, output_dir):
    print(f"✂️ Đang cắt PDF: {os.path.basename(pdf_path)}...")
    
    with open(json_flat_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f"   ❌ Lỗi đọc PDF: {e}")
        return

    count = 0
    for item in data:
        lid = item.get("Lid", "")
        st_str = item.get("St", "0")
        end_str = item.get("End", "0")
        
        if st_str.isdigit() and end_str.isdigit():
            st = int(st_str)
            end = int(end_str)
            
            if st > 0 and end >= st:
                writer = PdfWriter()
                # PyPDF2 tính từ 0, sách tính từ 1 -> st - 1
                for p in range(st - 1, end):
                    if p < len(reader.pages):
                        writer.add_page(reader.pages[p])
                
                # Tên file: ID.pdf (VD: 1_1_1.pdf)
                output_filename = f"{lid}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, "wb") as f_out:
                    writer.write(f_out)
                count += 1
    
    print(f"   ✅ Đã cắt {count} file vào: {output_dir}")

# ==============================================================================
# CHẠY CHƯƠNG TRÌNH
# ==============================================================================
if __name__ == "__main__":
    working_dir = r"D:\\NguVan\\C12_CTST"
    output_root = os.path.join(working_dir, "KetQua_Final")

    # Danh sách các cặp file cần xử lý
    tasks = [
        {
            "name": "SGK",
            "pdf": "SHS NGU VAN 12 TAP 2 CTST (Ruot ITB 06.02.25).pdf",
            "json": "SHS NGU VAN 12 TAP 2 CTST (Ruot ITB 06.02.25).json"
        },
        {
            "name": "SGV",
            "pdf": "SGV NGU VAN 12 TAP 2 CTST (IDT 21.05.24).pdf",
            "json": "SGV NGU VAN 12 TAP 2 CTST (IDT 21.05.24)_SGV.json"
        },
        {
            "name": "SBT",
            "pdf": "SBT NGU VAN 12 TAP 2 CTST (Ruot IDT 26.05.2024).pdf", # Hãy đảm bảo tên file PDF SBT của bạn đúng
            "json": "SBT NGU VAN 12 TAP 2 CTST (Ruot IDT 26.05.2024)_SBT.json"
        }
    ]

    for task in tasks:
        pdf_full_path = os.path.join(working_dir, task["pdf"])
        json_full_path = os.path.join(working_dir, task["json"])

        if os.path.exists(pdf_full_path) and os.path.exists(json_full_path):
            print(f"\n--- BẮT ĐẦU XỬ LÝ {task['name']} ---")
            # Bước 1: Tạo ID và Excel
            processed_json, out_dir = process_lesson_tree(pdf_full_path, json_full_path, output_root)
            
            # Bước 2: Cắt PDF
            cut_pdf_from_flat_json(pdf_full_path, processed_json, out_dir)
        else:
            print(f"\n⚠️ Bỏ qua {task['name']}: Thiếu file PDF hoặc JSON.")
            print(f"   - PDF: {pdf_full_path}")
            print(f"   - JSON: {json_full_path}")