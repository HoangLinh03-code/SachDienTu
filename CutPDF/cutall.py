import os, json
import openpyxl
from PyPDF2 import PdfReader, PdfWriter

listL = [
    "SDT_NGUVAN"
]
for itt in listL:
    rootfolder = r"D:\\pdf\\SDT_NGUVAN_KNTT_C11"
    process_folder = os.path.join(rootfolder, itt, f"{itt}_SGV đã fix")
    pdf_folder = os.path.join(rootfolder, itt, f"{itt}_SGV")
    for root, dirs, files in os.walk(process_folder):
        for f in files:
            if f.lower().endswith(".json"):
                output_path = os.path.join(rootfolder, "SDT", itt)
                file_path = os.path.join(root, f)
                print(f"Đang xử lý {f}...")
                with open(file_path, "r", encoding="utf-8") as d:
                    data = json.load(d)
                file_name = os.path.basename(file_path).replace(".json", "")
                pdf_path = os.path.join(pdf_folder, file_name, f"{file_name}.pdf")
                output_path = os.path.join(output_path, file_name)
                print(f"Xử lý {file_name}...")
                if not os.path.exists(output_path):
                    os.makedirs(output_path)

                # # Tạo file Excel
                # wb = openpyxl.Workbook()
                # ws = wb.active
                # ws.append(["", ""] + ["Name", "Lid"])
                # for item in data:
                #     row = ["", ""] + [item.get("Name", ""), item.get("Lid", "")]
                #     ws.append(row)
                # excel_path = os.path.join(output_path, f"{file_name}.xlsx")
                # wb.save(excel_path)
                # print(f"Đã tạo file Excel: {excel_path}")

                # Cắt file PDF
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
                        # Đặt tên file pdf nhỏ"
                        small_pdf_path = os.path.join(output_path, f"{lid}_SGV.pdf")
                        with open(small_pdf_path, "wb") as f_out:
                            writer.write(f_out)
                        print(f"Đã tạo file PDF: {small_pdf_path}")
                else:
                    print(f"Không tìm thấy file PDF: {pdf_path}")