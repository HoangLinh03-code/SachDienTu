import os

def rename_pdfs_to_nearest_folder(folder):
    for root, dirs, files in os.walk(folder):
        for file in files:
            old_path = os.path.join(root, file)
            # Tìm tên folder gần nhất chứa file
            nearest_folder = os.path.basename(os.path.dirname(old_path))
            # new_path = os.path.join(root, f"{nearest_folder}.pdf")
            new_path = old_path.replace("MYTHUATBAN2", "MYTHUAT")
            count = 1
            while os.path.exists(new_path):
                new_path = os.path.join(root, f"{nearest_folder}.pdf")
                count += 1
            os.rename(old_path, new_path)
            print(f"Đã đổi tên: {old_path} -> {new_path}")

if __name__ == "__main__":
    folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT_MYTHUAT"
    rename_pdfs_to_nearest_folder(folder)