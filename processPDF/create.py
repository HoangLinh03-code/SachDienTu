import json
import os
import openpyxl

def create_excel_like_sample(json_path, book_code, book_name, output_path):
    if not os.path.exists(json_path):
        print(f"❌ Không tìm thấy file JSON: {json_path}")
        return

    print(f"🎨 Đang tạo Excel theo mẫu 'bậc thang' cho: {book_code}...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cay Kien Thuc"
    
    # Tắt đường lưới để nhìn giống mẫu hơn (tuỳ chọn)
    ws.sheet_view.showGridLines = False 

    # --- GHI DÒNG ĐẦU TIÊN (TÊN SÁCH - CẤP 0) ---
    # Cấu trúc: "MÃ_SÁCH":"TÊN SÁCH" nằm ở Cột A (Cột 1)
    root_value = f"\"{book_code}\":\"{book_name}\""
    ws.cell(row=1, column=1, value=root_value)

    # Biến đếm dòng hiện tại (Bắt đầu từ dòng 2)
    current_row = 2

    # Hàm đệ quy để ghi dữ liệu
    def write_node(node_list, level, parent_id_str=""):
        nonlocal current_row
        
        for item in node_list:
            lid = str(item.get("Lid", ""))
            name = item.get("Name", "")
            
            # Tạo ID nối tiếp (VD: 1_1_1)
            # Nếu parent_id_str rỗng thì lấy lid, ngược lại nối thêm
            if parent_id_str:
                short_id = f"{parent_id_str}_{lid}"
            else:
                short_id = lid
            
            # Tạo Key đầy đủ (VD: SDT_NGUVAN_..._1_1)
            full_key = f"{book_code}_{short_id}"
            
            # Tạo nội dung ô theo format: "KEY":"VALUE"
            cell_content = f"\"{full_key}\":\"{name}\""
            
            # Ghi vào Excel
            # level là số cột cần ghi (Cấp 1 -> Cột 2, Cấp 2 -> Cột 3...)
            # Lưu ý: Root đã ở Cột 1, nên con của Root (Tập 1) sẽ ở Cột 2.
            ws.cell(row=current_row, column=level, value=cell_content)
            
            current_row += 1

            # Duyệt tiếp con (nếu có)
            if "Content" in item and isinstance(item["Content"], list):
                # Con sẽ thụt vào 1 cấp (level + 1)
                write_node(item["Content"], level + 1, short_id)

    # Bắt đầu duyệt từ dữ liệu JSON
    # Dữ liệu trong JSON (Tập 1) là con của Sách, nên bắt đầu từ Level 2 (Cột B)
    if isinstance(data, list):
        write_node(data, 2)
    elif isinstance(data, dict):
        write_node([data], 2)

    # Tự động chỉnh độ rộng cột cho dễ nhìn (tương đối)
    for col in range(1, 10):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 5

    wb.save(output_path)
    print(f"✅ Đã xuất file chuẩn mẫu: {output_path}")

if __name__ == "__main__":
    # ================= CẤU HÌNH =================
    
    # 1. Thư mục làm việc
    working_dir = r"D:\NguVan\C6_input"
    
    # 2. File JSON đầu vào (File SGK chuẩn)
    json_input = os.path.join(working_dir, "SHS Ngu van 6 tap 1 CTST (Ruot ITB 6.2.25).json")
    
    # 3. Mã sách (ROOT KEY) - Sửa lại cho đúng mã dự án của bạn
    # Trong ảnh mẫu là: SDT_NGUVAN_KNTT_C11 (Không có _1 ở cuối)
    my_book_code = "SDT_NGUVAN_CTST_C6" 
    
    # 4. Tên sách (ROOT NAME) - Hiển thị ở dòng đầu tiên
    my_book_name = "Ngữ văn lớp 6 bộ Chân trời sáng tạo"
    
    # 5. Tên file Excel đầu ra
    excel_output = os.path.join(working_dir, "CayKienThuc_CTST_C6.xlsx")

    # ============================================
    
    create_excel_like_sample(json_input, my_book_code, my_book_name, excel_output)


# import json
# import os
# import openpyxl

# def create_excel_tap2(json_path, book_code, book_name, output_path):
#     if not os.path.exists(json_path):
#         print(f"❌ Không tìm thấy file JSON: {json_path}")
#         return

#     print(f"🎨 Đang xử lý Tập 2 và tạo Excel cho: {book_code}...")
    
#     with open(json_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     # --- BƯỚC QUAN TRỌNG: SỬA LID TẬP 2 THÀNH "2" ---
#     # File JSON gốc đang để Lid="1", ta cần sửa thành "2" để ID ra đúng _2
#     if isinstance(data, list) and len(data) > 0:
#         if "Tập" in data[0].get("Name", ""):
#             print(f"   👉 Đã đổi ID '{data[0]['Name']}' từ {data[0]['Lid']} thành 2")
#             data[0]["Lid"] = "2" 

#     wb = openpyxl.Workbook()
#     ws = wb.active
#     ws.title = "Cay Kien Thuc"
#     ws.sheet_view.showGridLines = False 

#     # --- GHI DÒNG 1: TÊN SÁCH (CẤP 0) ---
#     # Cột A: "MÃ_SÁCH":"TÊN SÁCH"
#     root_value = f"\"{book_code}\":\"{book_name}\""
#     ws.cell(row=1, column=1, value=root_value)

#     current_row = 2

#     # Hàm đệ quy ghi dữ liệu
#     def write_node(node_list, level, parent_id_str=""):
#         nonlocal current_row
#         for item in node_list:
#             lid = str(item.get("Lid", ""))
#             name = item.get("Name", "")
            
#             # Tạo ID nối tiếp
#             if parent_id_str:
#                 short_id = f"{parent_id_str}_{lid}"
#             else:
#                 short_id = lid
            
#             # Tạo Key đầy đủ
#             full_key = f"{book_code}_{short_id}"
            
#             # Nội dung ô: "KEY":"VALUE"
#             cell_content = f"\"{full_key}\":\"{name}\""
            
#             # Ghi vào Excel (Thụt cột theo cấp độ)
#             # Root (Cấp 0) ở Cột 1 -> Tập (Cấp 1) ở Cột 2
#             ws.cell(row=current_row, column=level, value=cell_content)
            
#             current_row += 1

#             # Duyệt con
#             if "Content" in item and isinstance(item["Content"], list):
#                 write_node(item["Content"], level + 1, short_id)

#     # Bắt đầu duyệt (Level 2 = Cột B)
#     if isinstance(data, list):
#         write_node(data, 2)
#     elif isinstance(data, dict):
#         write_node([data], 2)

#     # Chỉnh độ rộng cột
#     for col in range(1, 12):
#         ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 5
    
#     wb.save(output_path)
#     print(f"✅ Đã xuất Excel chuẩn Tập 2: {output_path}")

# if __name__ == "__main__":
#     # --- CẤU HÌNH ---
#     working_dir = r"D:\NguVan\C6_input"
    
#     # 1. File JSON của Tập 2
#     json_file = os.path.join(working_dir, " SHS Ngu van 6 tap 1 CTST (Ruot ITB 6.2.25).json")
    
#     # 2. Mã sách chung (Lớp 12 Chân trời sáng tạo)
#     # Kết quả mong muốn: SDT_NGUVAN_CTST_C12_2 (Tập 2)
#     my_book_code = "SDT_NGUVAN_CTST_C6"
    
#     # 3. Tên sách hiển thị dòng đầu
#     my_book_name = "Ngữ văn lớp 6 bộ Chân trời sáng tạo"
    
#     # 4. Tên file Excel kết quả
#     excel_out = os.path.join(working_dir, "CayKienThuc_NV12_Tap1.xlsx")

#     # Chạy
#     create_excel_tap2(json_file, my_book_code, my_book_name, excel_out)