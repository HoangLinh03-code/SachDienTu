import os
import json
import shutil
import openpyxl
import unicodedata

# Hàm lột sạch dấu tiếng Việt
def remove_accents(input_str):
    return unicodedata.normalize('NFKD', input_str).encode('ASCII', 'ignore').decode('utf-8')

def finalize_project(working_dir, book_code, json_sgk_path):
    if not os.path.exists(working_dir):
        print(f"❌ Không tìm thấy thư mục: {working_dir}")
        return

    print(f"🚀 BẮT ĐẦU QUY TRÌNH FINALIZE CHO MÃ: {book_code}")

    # --- ĐỊNH TUYẾN THƯ MỤC THEO TÊN FOLDER ĐẦU VÀO ---
    parent_dir = os.path.dirname(working_dir)
    input_folder_name = os.path.basename(working_dir) 
    
    final_output_dir = os.path.join(parent_dir, "SDT_Done", input_folder_name)
    
    if not os.path.exists(final_output_dir):
        os.makedirs(final_output_dir)

    renamed_count = 0
    moved_count = 0

    # --- 1 & 2. TÌM KIẾM, ĐỔI TÊN (TIỀN TỐ + HẬU TỐ) VÀ GỘP FILE ---
    for root, dirs, files in os.walk(working_dir):
        if "SDT_Done" in root:
            continue
        
        root_no_accent = remove_accents(root).upper()
        
        # [NEW] CẬP NHẬT LOGIC NHẬN DIỆN ĐUÔI SÁCH ĐẦY ĐỦ (SGK / SBT / SGV)
        suffix = "SGK"  # Mặc định file đưa vào là Sách giáo khoa (SGK)
        
        if "SGV" in root_no_accent or "GIAO VIEN" in root_no_accent:
            suffix = "SGV"
        elif "SBT" in root_no_accent or "BAI TAP" in root_no_accent:
            suffix = "SBT"
        elif "SHS" in root_no_accent or "HOC SINH" in root_no_accent or "GIAO KHOA" in root_no_accent or "SGK" in root_no_accent:
            suffix = "SGK"

        for file_name in files:
            if file_name.lower().endswith(".pdf"):
                base_name, ext = os.path.splitext(file_name)
                
                # BƯỚC 1: Gắn hậu tố (_SGK, _SBT, _SGV)
                if suffix and not base_name.endswith(f"_{suffix}"):
                    base_name = f"{base_name}_{suffix}"
                
                # BƯỚC 2: Gắn TIỀN TỐ book_code lên đầu tên file
                if not base_name.startswith(book_code):
                    new_name = f"{book_code}_{base_name}{ext}"
                else:
                    new_name = f"{base_name}{ext}"
                
                src_path = os.path.join(root, file_name)
                dst_path = os.path.join(final_output_dir, new_name)
                
                try:
                    shutil.copy2(src_path, dst_path)
                    if new_name != file_name:
                        renamed_count += 1
                    moved_count += 1
                except Exception as e:
                    print(f"   ❌ Lỗi copy file {file_name}: {e}")

    print(f"   ✅ Đã gắn mã tiền tố và đổi tên cho {renamed_count} file PDF.")
    print(f"   ✅ Đã gom {moved_count} file PDF vào thư mục đích: {final_output_dir}")

    # --- 3. TẠO EXCEL TỔNG HỢP ---
    print("   ⏳ Đang tạo Excel đồng bộ...")
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
            full_id = f"{book_code}_{cur_id}" 
            
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

        excel_path = os.path.join(final_output_dir, f"{book_code}.xlsx")
        wb.save(excel_path)
        print(f"   ✅ Đã xuất Excel tổng hợp tại: {excel_path}")
        print("🎉 HOÀN TẤT QUY TRÌNH FINALIZE!")

    except Exception as e:
        print(f"❌ Lỗi khi xử lý JSON/Excel: {e}")