import json

# Đường dẫn file JSON của bạn
input_path = r'd:\NguVan\C6_input\SBT NGU VAN 6 TAP 1 CTST_SBT.json'
output_path = r'd:\NguVan\C6_input\SBT_NGU_VAN_6_TAP_1_CTST_Fixed.json'

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list) and len(data) > 0:
        root = data[0]
        # 1. Lọc bỏ Lid = "1" (Bài mở đầu)
        if "Content" in root:
            new_content = [item for item in root["Content"] if item.get("Lid") != "1"]
            
            # 2. Đánh số lại Lid từ 1 cho các bài còn lại
            for index, item in enumerate(new_content):
                item["Lid"] = str(index + 1)
            
            # 3. Cập nhật lại Content
            root["Content"] = new_content
            
            # 4. Lưu file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            print(f"✅ Đã sửa xong! File lưu tại: {output_path}")
            print(f"🔹 Tổng số bài học còn lại: {len(new_content)}")
            
    else:
        print("❌ Cấu trúc JSON không đúng định dạng.")

except Exception as e:
    print(f"❌ Lỗi: {e}")