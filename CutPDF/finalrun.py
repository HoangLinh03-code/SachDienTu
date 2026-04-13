import json
import os
import openpyxl
import re
from PyPDF2 import PdfReader, PdfWriter

# ==============================================================================
# PHẦN 1: LOGIC TẠO ID & EXCEL (Dựa trên processPDF/lessonTree.py)
# ==============================================================================
def process_lesson_tree(pdf_path, json_path, output_folder):
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    book_output_dir = os.path.join(output_folder, file_name)
    if not os.path.exists(book_output_dir):
        os.makedirs(book_output_dir)

    print(f"🔹 Đang xử lý cây kiến thức cho: {file_name}...")

    with open(json_path, "r", encoding="utf-8") as f:
        bookDatas = json.load(f)

    # =========================================================================
    # --- [NEW] FIX ID BẰNG REGEX TỰ ĐỘNG (BẮT CẢ SỐ VÀ CHỮ) ---
    # =========================================================================
    match = re.search(r't[aâậ]p[\s_\-]*(m[ộo]t|hai|ba|b[ốo]n|\d+)', file_name, re.IGNORECASE)
    
    if match:
        val = match.group(1).lower()
        mapping = {'một': '1', 'mot': '1', 'hai': '2', 'ba': '3', 'bốn': '4', 'bon': '4'}
        tap_number = mapping.get(val, val)
        print(f"   ⚠️ Phát hiện Sách TẬP {tap_number} -> Đang chuyển Root ID thành '{tap_number}'...")
    else:
        tap_number = "1"
        print(f"   ℹ️ Không phát hiện 'Tập X' trong tên, mặc định Root ID = '1'.")

    # Ép Lid của Node Gốc
    if isinstance(bookDatas, list) and len(bookDatas) > 0:
        bookDatas[0]["Lid"] = str(tap_number)
    elif isinstance(bookDatas, dict):
        bookDatas["Lid"] = str(tap_number)
    # ------------------------------

    # Tạo Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cay Kien Thuc"
    ws.append(["ID", "Tên Bài", "Trang Bắt Đầu", "Trang Kết Thúc"])

    lessons_flat_list = []

    # Hàm đệ quy duyệt cây và sinh ID
    def traverse_tree(data, parent_id=""):
        for item in data:
            Lid = str(item.get("Lid", ""))
            
            # Logic tạo ID: Nếu là Root (chưa có parent) thì lấy Lid (vd: "2")
            # Nếu có parent thì nối vào (vd: "2_1")
            cur_id = f"{parent_id}_{Lid}" if parent_id else Lid
            
            Name = item.get("Name", "")
            st = str(item.get("St", "0"))
            end = str(item.get("End", "0"))
            
            # Ghi vào Excel
            ws.append([cur_id, Name, st, end])

            if "Content" in item and isinstance(item["Content"], list) and item["Content"]:
                traverse_tree(item["Content"], cur_id)
            else:
                # Nút lá -> Thêm vào list để cắt
                if st != "0" and end != "0":
                    lessons_flat_list.append({
                        "Name": Name,
                        "Lid": cur_id, 
                        "St": st,
                        "End": end
                    })

    # Bắt đầu duyệt
    if isinstance(bookDatas, list):
        traverse_tree(bookDatas)
    elif isinstance(bookDatas, dict):
        traverse_tree([bookDatas])

    # Lưu Excel
    excel_path = os.path.join(book_output_dir, f"{file_name}.xlsx")
    wb.save(excel_path)
    print(f"   ✅ Đã tạo Excel: {excel_path}")

    # Lưu JSON phẳng
    json_flat_path = os.path.join(book_output_dir, f"{file_name}_processed.json")
    with open(json_flat_path, "w", encoding="utf-8") as f:
        json.dump(lessons_flat_list, f, ensure_ascii=False, indent=4)
    
    return json_flat_path, book_output_dir
# ==============================================================================
# PHẦN 2: LOGIC CẮT PDF (Dựa trên CutPDF/cutTap.py)
# ==============================================================================
def cut_pdf_from_flat_json(pdf_path, json_flat_path, output_dir, page_offset=0):
    print(f"✂️ Đang cắt PDF: {os.path.basename(pdf_path)} với Offset = {page_offset}...")
    
    with open(json_flat_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
    except Exception as e:
        print(f"   ❌ Lỗi đọc PDF: {e}")
        return

    count = 0
    for item in data:
        lid = item.get("Lid", "")
        st_str = str(item.get("St", "0"))
        end_str = str(item.get("End", "0"))
        
        if st_str.isdigit() and end_str.isdigit():
            st = int(st_str)
            end = int(end_str)
            
            if st > 0 and end >= st:
                writer = PdfWriter()
                
                # Thuật toán tính Index chuẩn xác:
                # Index PyPDF2 = Trang in (st) + Độ lệch (page_offset) - 1 (vì index mảng bắt đầu từ 0)
                start_idx = st + page_offset - 1
                end_idx = end + page_offset - 1 
                
                # Cắt từ start_idx đến end_idx (bao gồm cả end_idx nên cần + 1 trong hàm range)
                for p in range(start_idx, end_idx + 1):
                    if 0 <= p < total_pages:
                        writer.add_page(reader.pages[p])
                    else:
                        print(f"   ⚠️ Cảnh báo: Trang {p} vượt quá tổng số trang của PDF ({total_pages}).")
                
                output_filename = f"{lid}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, "wb") as f_out:
                    writer.write(f_out)
                count += 1
    
    print(f"   ✅ Đã cắt {count} file chuẩn xác vào: {output_dir}")

# ==============================================================================
# CHẠY CHƯƠNG TRÌNH
# ==============================================================================
if __name__ == "__main__":
    working_dir = r"D:\CheckTool\SachDienTu\SDT_Done\SachDienTu" # Chỉnh lại đường dẫn working dir của bạn
    output_root = os.path.join(working_dir, "KetQua_Final")

    # MỖI SÁCH SẼ CÓ MỘT ĐỘ LỆCH (OFFSET) KHÁC NHAU.
    # Công thức tính page_offset: 
    # Mở file PDF bằng trình xem PDF, nhảy đến trang in số 6, nhìn lên góc trên trình xem PDF xem nó là trang thứ mấy (ví dụ thứ 7).
    # page_offset = Trang Vật Lý (7) - Trang In (6) = 1.
    tasks = [
        {
            "name": "SGK Tieng Anh 6 Tap 1",
            "pdf": "D:\CheckTool\SachDienTu\drive-download-20260413T015814Z-3-001\SGK Tieng Anh 6 Tap 1- Global Success.pdf",
            "json": "D:\CheckTool\SachDienTu\drive-download-20260413T015814Z-3-001\SGK Tieng Anh 6 Tap 1- Global Success.json",
            "page_offset": 1  # <-- ĐIỀN ĐỘ LỆCH CỦA FILE PDF VÀO ĐÂY (Vd: 1)
        }
    ]

    for task in tasks:
        pdf_full_path = os.path.join(working_dir, task["pdf"])
        json_full_path = os.path.join(working_dir, task["json"])
        offset = task.get("page_offset", 0)

        if os.path.exists(pdf_full_path) and os.path.exists(json_full_path):
            print(f"\n--- BẮT ĐẦU XỬ LÝ {task['name']} ---")
            processed_json, out_dir = process_lesson_tree(pdf_full_path, json_full_path, output_root)
            
            # Truyền thêm tham số offset vào hàm cắt
            cut_pdf_from_flat_json(pdf_full_path, processed_json, out_dir, page_offset=offset)
        else:
            print(f"\n⚠️ Bỏ qua {task['name']}: Thiếu file PDF hoặc JSON.")