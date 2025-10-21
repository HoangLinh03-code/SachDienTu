import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import fitz  # PyMuPDF
import unicodedata
import io

# Nếu cần, chỉ định đường dẫn Tesseract (bỏ comment nếu gặp lỗi 'tesseract not found')
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Chỉnh cho Windows

def pdf_to_images(pdf_path):
    """Chuyển PDF thành danh sách ảnh."""
    try:
        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(800/72, 800/72))  # Độ phân giải 300 DPI
            # Chuyển Pixmap thành bytes và tạo Image
            img_data = pix.tobytes("png")  # Lấy dữ liệu ảnh định dạng PNG
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        doc.close()
        return images
    except Exception as e:
        print(f"Lỗi khi chuyển PDF sang ảnh {pdf_path}: {e}")
        return []

def convert_pdf_to_md(pdf_path, md_path):
    """Chuyển PDF sang Markdown với OCR."""
    try:
        # Chuyển PDF thành ảnh và OCR
        images = pdf_to_images(pdf_path)
        text = ""
        for img in images:
            # OCR với ngôn ngữ tiếng Việt
            img = img.convert('L')  # Chuyển sang grayscale
            img = ImageEnhance.Contrast(img).enhance(2.0)  # Tăng độ tương phản
            img = img.filter(ImageFilter.SHARPEN)  # Làm sắc nét
            page_text = pytesseract.image_to_string(img, lang='vie', config='--psm 3 --oem 3')
            if page_text:
                # Chuẩn hóa Unicode để sửa lỗi font tiếng Việt
                page_text = unicodedata.normalize('NFKC', page_text)
                text += page_text + "\n\n"
        
        # Lưu file với UTF-8
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"Lỗi khi xử lý {pdf_path}: {e}")

# Đường dẫn thư mục
root_dir = 'SDT'  # Thay đổi nếu thư mục ở nơi khác
output_dir = 'SDT_DONE'
os.makedirs(output_dir, exist_ok=True)

# Duyệt thư mục
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.lower().endswith('.pdf'):
            pdf_path = os.path.join(subdir, file)
            leaf_folder = os.path.basename(subdir)
            target_dir = os.path.join(output_dir, leaf_folder)
            os.makedirs(target_dir, exist_ok=True)
            md_file = file.replace('.pdf', '.md')
            md_path = os.path.join(target_dir, md_file)
            convert_pdf_to_md(pdf_path, md_path)
            print(f"Đã chuyển {pdf_path} sang {md_path}")

print("Hoàn tất! Kiểm tra thư mục SDT_DONE.")