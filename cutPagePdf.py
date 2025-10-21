import os
from PyPDF2 import PdfReader, PdfWriter
import shutil

def extract_pdf_pages(input_pdf, output_pdf, pages):
    """
    Xuất các trang mong muốn từ file PDF.
    - input_pdf: đường dẫn file PDF gốc
    - output_pdf: đường dẫn file PDF xuất ra
    - pages: list các số trang muốn xuất (bắt đầu từ 1)
    """
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    for p in pages:
        if 1 <= p <= len(reader.pages):
            writer.add_page(reader.pages[p-1])
    with open(output_pdf, "wb") as f_out:
        writer.write(f_out)
    print(f"Đã xuất các trang {pages} ra file: {output_pdf}")

    # Chuyển file PDF ban đầu qua tmp_folder
    tmp_folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu"
    if os.path.exists(input_pdf):
        shutil.move(input_pdf, os.path.join(tmp_folder, os.path.basename(input_pdf)))
        print(f"Đã chuyển file gốc vào {tmp_folder}")

if __name__ == "__main__":
    input_pdf = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT_TOAN\SDT_TOAN_SGK\SDT_TOANTAP2_CTST_C2\SDT_TOANTAP2_CTST_C2.pdf"
    tmp_folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu"
    file_name = os.path.basename(input_pdf).replace(".pdf", "") + "-trang.pdf"
    output_pdf = os.path.join(os.path.dirname(input_pdf), file_name)
    pages_to_export = [5]
    extract_pdf_pages(input_pdf, output_pdf, pages_to_export)