import subprocess
import os

def compress_pdf_ghostscript(input_path, output_path, quality='screen'):
    """
    Nén file PDF bằng Ghostscript.
    quality options:
    - screen: 72dpi, nhỏ nhất
    - ebook: 150dpi, vừa phải 
    - printer: 300dpi, chất lượng cao
    - prepress: 300dpi, chất lượng tốt nhất
    """
    if not os.path.isfile(input_path):
        print(f"File nguồn không tồn tại: {input_path}")
        return False

    gs_command = [
        'gswin64c',
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        f'-dPDFSETTINGS=/{quality}',
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        f'-sOutputFile={output_path}',
        input_path
    ]

    try:
        subprocess.run(gs_command, check=True, capture_output=True, text=True)
        print(f"Nén thành công: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print("Lỗi khi nén PDF:")
        print(e)
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return False

def compress_folder(folder, quality='screen'):
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".pdf"):
                file_path = os.path.join(root, file)
                print(f"Đang nén file: {file_path}")
                output_path = os.path.join(root, f"compressed_{file}")
                if compress_pdf_ghostscript(file_path, output_path, quality):
                    try:
                        os.remove(file_path)
                        os.rename(output_path, file_path)
                        print(f"Đã ghi đè file: {file_path}")
                    except Exception as e:
                        print(f"Lỗi khi ghi đè file: {file_path} - {e}")

if __name__ == "__main__":
    folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SGV\KNTT"
    compress_folder(folder, quality='ebook')