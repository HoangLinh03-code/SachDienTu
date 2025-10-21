import os
import shutil
import re

# Thư mục gốc chứa các folder TAP1, TAP2
root_folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT\SDT_NGUVAN"

# Thư mục đích để lưu các folder gom lại
done_root = root_folder + "_DONE"
os.makedirs(done_root, exist_ok=True)

# Duyệt tất cả folder con trong SDT_TOAN
for subfolder in os.listdir(root_folder):
    subfolder_path = os.path.join(root_folder, subfolder)
    if not os.path.isdir(subfolder_path):
        continue

    # Nhận diện tên dạng SDT_TOANTAP1_CTST_C1 hoặc SDT_TOANTAP2_KNTT_C2
    match = re.match(r"(SDT_[A-Z]+)TAP[12]_([A-Z]+)_C(\d+)", subfolder)
    if match:
        base_name = match.group(1)      # SDT_TOAN
        code = match.group(2)           # CTST hoặc KNTT
        class_num = match.group(3)      # 1, 2, 3,...
        target_folder_name = f"{base_name}_{code}_C{class_num}"
        target_folder = os.path.join(done_root, target_folder_name)

        os.makedirs(target_folder, exist_ok=True)

        # Copy các file PDF trong folder hiện tại
        for file in os.listdir(subfolder_path):
            if file.lower().endswith(".pdf"):
                src = os.path.join(subfolder_path, file)
                dst = os.path.join(target_folder, file)

                # Tránh trùng tên file
                if os.path.exists(dst):
                    name, ext = os.path.splitext(file)
                    i = 1
                    while os.path.exists(os.path.join(target_folder, f"{name}_{i}{ext}")):
                        i += 1
                    dst = os.path.join(target_folder, f"{name}_{i}{ext}")

                shutil.copy2(src, dst)
                print(f"✅ Copy: {file} → {target_folder_name}")

print("\n🎉 Hoàn tất! Tất cả file PDF đã được gom vào thư mục:")
print(done_root)
