import os, json

tap2_folder = r'C:\Users\Admin\Desktop\Maru\SachDienTu\SDT_TOAN\SDT_TOAN_SGK đã fix'
for root, dirs, files in os.walk(tap2_folder):
    for f in files:
        if f.lower().endswith(".json"):
            json_path = os.path.join(root, f)
            file_name = os.path.splitext(os.path.basename(f))[0]
            print(f"Đang xử lý file: {file_name}")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "TAP1" in file_name:
                for item in data:
                    old_lid = item.get("Lid", "")
                    new_lid = old_lid.replace(file_name, f"{file_name}_1").replace("TAP1" , "")
                    item["Lid"] = new_lid
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif "TAP2" in file_name:
                for item in data:
                    old_lid = item.get("Lid", "")
                    new_lid = old_lid.replace(file_name, f"{file_name}_2").replace("TAP2" , "")
                    item["Lid"] = new_lid
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Đã xử lý xong: {file_name}")