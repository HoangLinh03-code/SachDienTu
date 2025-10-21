import os, json
import openpyxl
from PyPDF2 import PdfReader, PdfWriter

rootfolder = r"C:\Users\Admin\Desktop\Maru\SachDienTu"

listL = [
    "SDT_TOAN"
]

for itt in listL:
    # Tìm tất cả folder con có tên bắt đầu bằng itt (ví dụ: SDT_NGUVANTAP1, SDT_NGUVANTAP2, ...)
    matched_folders = [f for f in os.listdir(rootfolder) if f.startswith(itt)]
    if not matched_folders:
        print(f"⚠️ Không tìm thấy thư mục nào bắt đầu bằng {itt}")
        continue

    for subfolder in matched_folders:
        process_folder = os.path.join(rootfolder, subfolder, f"{subfolder}_SGV đã fix")
        pdf_folder = os.path.join(rootfolder, subfolder, f"{subfolder}_SGV")

        if not os.path.exists(process_folder):
            print(f"⛔ Bỏ qua: không tìm thấy {process_folder}")
            continue

        for root, dirs, files in os.walk(process_folder):
            for f in files:
                if f.lower().endswith(".json"):
                    output_path = os.path.join(rootfolder, "SDT", subfolder)
                    file_path = os.path.join(root, f)
                    print(f"📘 Đang xử lý {f} trong {subfolder}...")

                    with open(file_path, "r", encoding="utf-8") as d:
                        data = json.load(d)

                    file_name = os.path.splitext(f)[0]
                    pdf_path = os.path.join(pdf_folder, file_name, f"{file_name}.pdf")
                    output_path = os.path.join(output_path, file_name)

                    if not os.path.exists(output_path):
                        os.makedirs(output_path)

                    # --- Cắt file PDF ---
                    if os.path.exists(pdf_path):
                        reader = PdfReader(pdf_path)
                        for item in data:
                            name = item.get("Name", "")
                            lid = item.get("Lid", "")
                            st = int(item.get("St", 1))
                            end = int(item.get("End", st))
                            writer = PdfWriter()
                            for p in range(st, end + 1):
                                if 1 <= p <= len(reader.pages):
                                    writer.add_page(reader.pages[p - 1])
                            small_pdf_path = os.path.join(output_path, f"{lid}_SGV.pdf")
                            with open(small_pdf_path, "wb") as f_out:
                                writer.write(f_out)
                            print(f"✅ Đã tạo file PDF: {small_pdf_path}")
                    else:
                        print(f"❌ Không tìm thấy file PDF: {pdf_path}")
