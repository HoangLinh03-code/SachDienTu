import os
import shutil

# Đường dẫn tới folder chứa PDF
pdf_folder = r"C:\Users\Admin\Desktop\Maru\SachDienTu\SGK\CTST\Lớp 12"

def organize_pdfs(folder_path):
    # Lấy danh sách file pdf trong folder
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    
    for pdf in pdf_files:
        # Tách tên file (không bao gồm .pdf)
        pdf_name = os.path.splitext(pdf)[0]
        
        # Tạo folder con theo tên file
        new_folder = os.path.join(folder_path, pdf_name)
        os.makedirs(new_folder, exist_ok=True)
        
        # Đường dẫn gốc và đích
        src = os.path.join(folder_path, pdf)
        dst = os.path.join(new_folder, pdf)
        
        # Di chuyển file vào folder
        shutil.move(src, dst)
        print(f"Đã chuyển {pdf} vào {new_folder}")

organize_pdfs(pdf_folder)