import os
import json
from pathlib import Path

root = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT_TOAN\SDT_TOAN_SGK đã fix"
out_root = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT_TOAN\SDT_TOAN_SGK đã fix done"

os.makedirs(out_root, exist_ok=True)

# Lấy danh sách folder con
subfolders = [f for f in os.listdir(root) if os.path.isdir(os.path.join(root, f))]

# Gom các cặp TAP1 - TAP2
pairs = {}
for folder in subfolders:
    if not folder.startswith("SDT_TOANTAP"):
        continue
    parts = folder.split("_")
    # parts = ['SDT', 'TOANTAP1', 'CTST', 'C2']
    tap = parts[1]  # TOANTAP1 hoặc TOANTAP2
    subject_code = "_".join(parts[2:])  # CTST_C2
    pairs.setdefault(subject_code, {})[tap] = folder

# Xử lý từng cặp
for code, taps in pairs.items():
    tap1_folder = taps.get("TOANTAP1")
    tap2_folder = taps.get("TOANTAP2")
    if not (tap1_folder and tap2_folder):
        print(f"⚠️ Bỏ qua {code}: thiếu 1 trong 2 TAP.")
        continue

    tap1_json_path = os.path.join(root, tap1_folder, f"{tap1_folder}.json")
    tap2_json_path = os.path.join(root, tap2_folder, f"{tap2_folder}.json")

    if not (os.path.exists(tap1_json_path) and os.path.exists(tap2_json_path)):
        print(f"⚠️ Bỏ qua {code}: thiếu file json.")
        continue

    with open(tap1_json_path, "r", encoding="utf-8") as f1:
        data1 = json.load(f1)
    with open(tap2_json_path, "r", encoding="utf-8") as f2:
        data2 = json.load(f2)

    # Nối dữ liệu
    merged_data = data1 + data2

    # Tạo folder output
    out_folder = os.path.join(out_root, f"SDT_TOAN_{code}")
    os.makedirs(out_folder, exist_ok=True)
    out_path = os.path.join(out_folder, f"SDT_TOAN_{code}.json")

    with open(out_path, "w", encoding="utf-8") as f_out:
        json.dump(merged_data, f_out, ensure_ascii=False, indent=2)

    print(f"✅ Đã ghép xong: {code}")

print("🎉 Hoàn tất tất cả!")
