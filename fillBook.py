import os
import shutil

# Đường dẫn các thư mục
SDT_DONE = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT_DONE"
SDT = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT"
MATHPIX_TMP = r"C:\Users\Admin\Desktop\Maru\SachDienTu\MathPix Tmp"

os.makedirs(MATHPIX_TMP, exist_ok=True)

# Hàm lấy danh sách tên file không kèm đuôi
def list_files_no_ext(folder, ext):
    result = {}
    for root, _, files in os.walk(folder):
        rel_dir = os.path.relpath(root, folder)
        result[rel_dir] = set(os.path.splitext(f)[0] for f in files if f.lower().endswith(ext))
    return result

# Lấy danh sách file md và pdf
md_files = list_files_no_ext(SDT_DONE, ".md")
pdf_files = list_files_no_ext(SDT, ".pdf")

# So sánh từng thư mục con
for rel_dir, pdf_set in pdf_files.items():
    md_set = md_files.get(rel_dir, set())
    missing_pdfs = pdf_set - md_set  # file pdf chưa có bản md tương ứng

    if missing_pdfs:
        src_dir = os.path.join(SDT, rel_dir)
        for pdf_name in missing_pdfs:
            src_path = os.path.join(src_dir, pdf_name + ".pdf")
            if os.path.exists(src_path):
                shutil.copy(src_path, MATHPIX_TMP)
                print(f"✅ Copied: {pdf_name}.pdf")

print("🎯 Hoàn tất so sánh và copy các file PDF còn thiếu!")
