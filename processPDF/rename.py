# import os

# def rename_pdfs_to_nearest_folder(folder):
#     for root, dirs, files in os.walk(folder):
#         for file in files:
#             old_path = os.path.join(root, file)
#             # Tìm tên folder gần nhất chứa file
#             nearest_folder = os.path.basename(os.path.dirname(old_path))
#             # new_path = os.path.join(root, f"{nearest_folder}.pdf")
#             new_path = old_path.replace("MYTHUATBAN2", "MYTHUAT")
#             count = 1
#             while os.path.exists(new_path):
#                 new_path = os.path.join(root, f"{nearest_folder}.pdf")
#                 count += 1
#             os.rename(old_path, new_path)
#             print(f"Đã đổi tên: {old_path} -> {new_path}")

# if __name__ == "__main__":
#     folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT_MYTHUAT"
#     rename_pdfs_to_nearest_folder(folder)

import os

def rename_files_with_type(working_dir, book_code):
    # Thư mục gốc chứa các folder con
    root_cut_dir = os.path.join(working_dir, "KetQua_Final")
    
    # 3 loại sách cần xử lý
    book_types = ["SGK", "SGV", "SBT"]
    
    print(f"🚀 Bắt đầu đổi tên file cho mã: {book_code}")

    for b_type in book_types:
        folder_path = os.path.join(root_cut_dir, b_type)
        if not os.path.exists(folder_path):
            print(f"⚠️ Không thấy thư mục {b_type}, bỏ qua.")
            continue
            
        print(f"\n📂 Đang xử lý: {b_type}...")
        count = 0
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf") and book_code not in filename:
                # Tên cũ: 1_1_1.pdf
                old_path = os.path.join(folder_path, filename)
                id_part = os.path.splitext(filename)[0]
                
                # Tên mới: SDT_..._1_1_1_SGK.pdf (Thêm đuôi loại sách ở đây)
                new_name = f"{book_code}_{id_part}_{b_type}.pdf"
                new_path = os.path.join(folder_path, new_name)
                
                try:
                    os.rename(old_path, new_path)
                    count += 1
                except Exception as e:
                    print(f"   Lỗi: {e}")
                    
        print(f"   ✅ Đã đổi tên {count} file (Đuôi _{b_type})")

if __name__ == "__main__":
    # Sửa đường dẫn và mã sách của bạn ở đây
    rename_files_with_type(r"D:\\NguVan", "SDT_NGUVAN_KNTT_C11")