import os
import json
import shutil
import openpyxl

def finalize_project(working_dir, book_code, json_sgk_path):
    # Thư mục chứa các file đã cắt
    cut_dir = os.path.join(working_dir, "KetQua_Final")
    
    if not os.path.exists(cut_dir):
        print(f"❌ Không tìm thấy thư mục kết quả cắt: {cut_dir}")
        return

    print(f"🚀 BẮT ĐẦU QUY TRÌNH FINALIZE CHO MÃ: {book_code}")

    # --- 1. ĐỔI TÊN FILE (SMART RENAME) ---
    renamed_count = 0
    
    # Duyệt tất cả các thư mục con trong KetQua_Final
    if os.path.exists(cut_dir):
        for folder_name in os.listdir(cut_dir):
            folder_path = os.path.join(cut_dir, folder_name)
            
            # Chỉ xử lý nếu là thư mục
            if not os.path.isdir(folder_path):
                continue

            # --- LOGIC NHẬN DIỆN THÔNG MINH ---
            name_upper = folder_name.upper()
            suffix = ""
            
            if "SGV" in name_upper or "GIAO VIEN" in name_upper:
                suffix = "SGV"
            elif "SBT" in name_upper or "BAI TAP" in name_upper:
                suffix = "SBT"
            elif "SGK" in name_upper or "SHS" in name_upper or "GIAO KHOA" in name_upper:
                suffix = "SGK"
            
            # Nếu không xác định được loại sách -> Bỏ qua
            if not suffix:
                print(f"⚠️ Bỏ qua folder không xác định: {folder_name}")
                continue

            print(f"📂 Đang xử lý folder: '{folder_name}' -> Loại: {suffix}")
            
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(".pdf"):
                    # Nếu tên file chưa chứa mã sách (chưa đổi tên)
                    if book_code not in filename:
                        old_path = os.path.join(folder_path, filename)
                        id_part = os.path.splitext(filename)[0]
                        
                        # Tên mới: MA_SACH + ID + LOAI.pdf
                        new_filename = f"{book_code}_{id_part}_{suffix}.pdf"
                        new_path = os.path.join(folder_path, new_filename)
                        
                        try:
                            os.rename(old_path, new_path)
                            renamed_count += 1
                        except Exception as e:
                            print(f"   ❌ Lỗi đổi tên {filename}: {e}")
    
    print(f"✅ Đã đổi tên thành công {renamed_count} file.")

    # --- 2. TẠO EXCEL TỔNG HỢP ---
    print("\n📊 Đang tạo file Excel Cây kiến thức...")
    if not os.path.exists(json_sgk_path):
        print("❌ Không tìm thấy file JSON SGK.")
        return

    try:
        with open(json_sgk_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Cay Kien Thuc"
        ws.append(["ID Đầy Đủ", "Tên Bài", "Cấp độ", "Trang SGK"])

        def write_node(node, parent_id=""):
            lid = str(node.get("Lid", ""))
            cur_id = f"{parent_id}_{lid}" if parent_id else lid
            full_id = f"{book_code}_{cur_id}" # ID đầy đủ
            
            name = node.get("Name", "")
            st = node.get("St", "")
            end = node.get("End", "")
            level = len(cur_id.split('_'))
            page_info = f"{st}-{end}" if (st and st != "0") else ""
            
            ws.append([full_id, name, level, page_info])

            if "Content" in node:
                for child in node["Content"]:
                    write_node(child, cur_id)

        if isinstance(data, list):
            for item in data: write_node(item)
        elif isinstance(data, dict):
            write_node(data)

        excel_name = f"{book_code}.xlsx"
        excel_path = os.path.join(working_dir, excel_name)
        wb.save(excel_path)
        print(f"✅ Đã xuất Excel tổng: {excel_path}")

    except Exception as e:
        print(f"❌ Lỗi tạo Excel: {e}")

if __name__ == "__main__":
    # Test thử nếu chạy trực tiếp
    pass