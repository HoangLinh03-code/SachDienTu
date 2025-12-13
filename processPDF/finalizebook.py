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

    print("🚀 BẮT ĐẦU ĐỔI TÊN FILE VÀ TẠO EXCEL...")

    # --- 1. ĐỔI TÊN FILE ---
    subfolders = ["SGK", "SGV", "SBT"]
    for sub in subfolders:
        folder_path = os.path.join(cut_dir, sub)
        if os.path.exists(folder_path):
            print(f"\n📂 Đang xử lý thư mục: {sub}...")
            count = 0
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(".pdf"):
                    # Nếu file đã có mã sách thì bỏ qua (tránh đổi tên 2 lần)
                    if book_code in filename:
                        continue

                    old_path = os.path.join(folder_path, filename)
                    id_part = os.path.splitext(filename)[0]
                    
                    # Tạo tên mới chuẩn: MA_SACH + ID + LOAI_SACH.pdf
                    new_filename = f"{book_code}_{id_part}_{sub}.pdf"
                    new_path = os.path.join(folder_path, new_filename)
                    
                    try:
                        os.rename(old_path, new_path)
                        count += 1
                    except Exception as e:
                        print(f"   ⚠️ Lỗi đổi tên {filename}: {e}")
            print(f"   ✅ Đã đổi tên {count} file.")

    # --- 2. TẠO EXCEL ---
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

        # Lưu Excel ra thư mục gốc
        excel_name = f"{book_code}.xlsx"
        excel_path = os.path.join(working_dir, excel_name)
        wb.save(excel_path)
        print(f"✅ Đã xuất Excel: {excel_path}")

    except Exception as e:
        print(f"❌ Lỗi tạo Excel: {e}")

if __name__ == "__main__":
    # --- CẤU HÌNH (Sửa theo ảnh bạn gửi) ---
    
    # 1. Thư mục chứa folder KetQua_Final (Ổ D:\NguVan)
    my_work_dir = r"D:\\NguVan\\C12_CTST"
    
    # 2. Mã sách (Dùng để đặt tên file)
    # Ví dụ: SDT_NGUVAN_KNTT_C11_1 (Ngữ văn 11 Tập 1 KNTT)
    # Bạn hãy sửa lại mã này cho đúng quy định dự án
    my_book_code = "SDT_NGUVAN_CTST_C12_2" 
    
    # 3. Tên file JSON SGK chuẩn (để lấy dữ liệu tạo Excel)
    my_json_sgk = os.path.join(my_work_dir, "SHS NGU VAN 12 TAP 2 CTST (Ruot ITB 06.02.25).json")

    finalize_project(my_work_dir, my_book_code, my_json_sgk)