import os
import shutil

listL = [
    "SDT_GDKTPL", "SDT_GDQP", "SDT_GDTC", "SDT_GDTCBONGCHUYEN", "SDT_GDTCBONGDA",
    "SDT_GDTCBONGRO", "SDT_GDTCCAULONG", "SDT_HDTN", "SDT_HOAHOC", "SDT_KHOAHOC",
    "SDT_KHTN", "SDT_LICHSU", "SDT_LICHSUDIALI", "SDT_MYTHUAT", "SDT_NGUVAN",
    "SDT_SINHHOC", "SDT_TIENGVIET", "SDT_TINHOC", "SDT_TINHOCKHMT", "SDT_TINHOCUD",
    "SDT_TNHN", "SDT_TOAN", "SDT_TUNHIENVAXAHOI", "SDT_VATLY"
]

sgk_folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SGV"

for code in listL:
    folder_out = os.path.join(r"C:\Users\Admin\Desktop\Maru\SachDienTu", code)
    sgk_out = os.path.join(folder_out, f"{code}_SGV")
    if not os.path.exists(sgk_out):
        os.makedirs(sgk_out)
    # Quét tất cả các folder con bên trong SGK (bao gồm nhiều cấp)
    for root, dirs, files in os.walk(sgk_folder):
        for d in dirs:
            if code in d:
                src_path = os.path.join(root, d)
                dest_path = os.path.join(sgk_out, d)
                if not os.path.exists(dest_path):
                    shutil.move(src_path, dest_path)
                    print(f"Đã chuyển {src_path} vào {dest_path}")