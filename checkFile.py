import os
import json

sbt_folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SBT đã cắt\KNTT\Lớp 12"
sgk_folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SGK đã cắt\KNTT\Lớp 12"

for root, dirs, files in os.walk(sbt_folder):
    for f in files:
        if f.lower().endswith(".json"):
            sbt_json_path = os.path.join(root, f)
            file_name = os.path.splitext(os.path.basename(f))[0]
            sgk_json_path = os.path.join(f"{sgk_folder}\{file_name}", f)
            if os.path.exists(sgk_json_path):
                with open(sbt_json_path, "r", encoding="utf-8") as sbt_file:
                    sbt_data = json.load(sbt_file)
                with open(sgk_json_path, "r", encoding="utf-8") as sgk_file:
                    sgk_data = json.load(sgk_file)
                
                if len(sbt_data) - len(sgk_data) > 5 or len(sgk_data) - len(sbt_data) > 5:
                    print(f"⚠ File {file_name}.")
                else:
                    count = 0
                    lesson = []
                    for item in sgk_data:
                        lesson.append(item["Name"])
                    for item in sbt_data:
                        if item["Name"] not in lesson:
                            count += 1
                    if count > 5:
                        print(f"⚠ File {file_name}.")