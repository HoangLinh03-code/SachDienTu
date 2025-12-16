import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
import threading
import subprocess
import platform
from dotenv import load_dotenv

# --- CẤU HÌNH IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
for folder in ['API', 'CutPDF', 'processPDF', 'takeMenu', 'processMd']:
    sys.path.append(os.path.join(current_dir, folder))

load_dotenv(os.path.join(current_dir, 'API', '.env'))

# --- IMPORT CÁC HÀM XỬ LÝ ---
try:
    from takeMenu.forceDeepScanAI import extract_strict_structure
    from takeMenu.smart_toc import scan_toc_large_file
    from processPDF.create import create_excel_like_sample
    from processPDF.sync_sgv_sbt import sync_book_menu
    from CutPDF.finalrun import process_lesson_tree, cut_pdf_from_flat_json
    from processPDF.finalizebook import finalize_project
    from processMd.pdfToMdAI import getBookMenuFromAI as pdfToMdAI_Convert
except ImportError as e:
    print(f"⚠️ Cảnh báo thiếu file nguồn: {e}")

class SachDienTuManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản Lý Sách Điện Tử (Smart Rename Support)")
        self.root.geometry("950x750")

        tabControl = ttk.Notebook(root)
        self.tabs = {}
        step_names = [
            ('tab1', '1. Tạo JSON Mục Lục'),
            ('tab2', '2. Tạo Excel (Tree)'),
            ('tab3', '3. Đồng bộ SGV/SBT'),
            ('tab4', '4. Cắt PDF'),
            ('tab5', '5. Đổi tên & Final'),
            ('tab6', '6. Tạo Markdown')
        ]
        
        for name, label in step_names:
            frame = ttk.Frame(tabControl)
            tabControl.add(frame, text=label)
            self.tabs[name] = frame

        tabControl.pack(expand=1, fill="both")

        self.setup_tab1()
        self.setup_tab2()
        self.setup_tab3()
        self.setup_tab4()
        self.setup_tab5()
        self.setup_tab6()

    # --- HELPER FUNCTIONS ---
    def open_path(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Lỗi", f"Không tìm thấy:\n{path}")
            return
        try:
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": subprocess.call(["open", path])
            else: subprocess.call(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Lỗi mở file", str(e))

    def add_ui_row(self, tab, label_text, row, is_file=True, var=None):
        tk.Label(tab, text=label_text, font=('Arial', 9, 'bold')).grid(column=0, row=row, padx=10, pady=10, sticky='W')
        if var is None: var = tk.StringVar()
        entry = tk.Entry(tab, width=65, textvariable=var)
        entry.grid(column=1, row=row, padx=10, pady=10)
        def browse():
            if is_file: filename = filedialog.askopenfilename()
            else: filename = filedialog.askdirectory()
            if filename: var.set(filename)
        btn = tk.Button(tab, text="📂 Chọn", command=browse)
        btn.grid(column=2, row=row, padx=5, pady=10)
        return var
    
    def browse_file(self, var):
        filename = filedialog.askopenfilename()
        if filename: var.set(filename)

    # --- AUTO FIX JSON ---
    def auto_fix_json_logic(self, json_path, label=""):
        if not os.path.exists(json_path): return False
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            log_changes = []
            last_end = 0
            def traverse_and_fix(items):
                nonlocal last_end
                for item in items:
                    if "Content" in item: traverse_and_fix(item["Content"])
                    else:
                        try: st, end = int(item.get("St", 0)), int(item.get("End", 0))
                        except: st, end = 0, 0
                        orig_st, orig_end = st, end
                        changed = False
                        if st > end and end != 0:
                            st, end = end, st
                            changed = True
                            log_changes.append(f"🔄 {item.get('Name','...')[:20]}: Đảo ({orig_st}-{orig_end} -> {st}-{end})")
                        if st > 0 and st <= last_end:
                            new_st = last_end + 1
                            if new_st > end: end = new_st 
                            st = new_st
                            changed = True
                            log_changes.append(f"⬆️ {item.get('Name','...')[:20]}: Đẩy ({orig_st} -> {st}) do trùng.")
                        if changed:
                            item["St"] = str(st)
                            item["End"] = str(end)
                        if end > last_end: last_end = end
            if isinstance(data, list): traverse_and_fix(data)
            elif isinstance(data, dict): traverse_and_fix([data])
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            if log_changes:
                msg = f"[{label}] Đã sửa:\n" + "\n".join(log_changes)
                messagebox.showinfo(f"Fix {label}", msg)
            return True
        except Exception as e:
            messagebox.showerror("Lỗi Fix", str(e))
            return False

    # --- TAB 1 ---
    def setup_tab1(self):
        self.t1_pdf_path = self.add_ui_row(self.tabs['tab1'], "File PDF Gốc:", 0)
        btn_frame = tk.Frame(self.tabs['tab1'])
        btn_frame.grid(column=1, row=2, pady=20)
        tk.Button(btn_frame, text="▶ 1. CHẠY AI", bg="#90EE90", command=self.run_step1).pack(side=tk.LEFT, padx=5)
        # tk.Button(btn_frame, text="🛠 2. AUTO FIX LOGIC", bg="#FFA07A", command=self.run_fix_tab1).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="👁 3. KIỂM TRA", bg="#FFD700", command=self.check_step1).pack(side=tk.LEFT, padx=5)
        self.t1_status = tk.Label(self.tabs['tab1'], text="...", fg="blue")
        self.t1_status.grid(column=1, row=3)

    def run_step1(self):
        pdf_path = self.t1_pdf_path.get()
        if not os.path.exists(pdf_path): return
        def task():
            try:
                self.t1_status.config(text="Đang xử lý...")
                file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
                file_name = os.path.splitext(os.path.basename(pdf_path))[0]
                if file_size_mb > 30: scan_toc_large_file(pdf_path)
                else: extract_strict_structure(file_name, pdf_path)
                self.t1_status.config(text="✅ Xong.")
                messagebox.showinfo("Xong", "Đã tạo JSON.")
            except Exception as e: messagebox.showerror("Lỗi", str(e))
        threading.Thread(target=task).start()

    def run_fix_tab1(self):
        pdf_path = self.t1_pdf_path.get()
        json_path = os.path.splitext(pdf_path)[0] + ".json"
        if self.auto_fix_json_logic(json_path, "Mục Lục"): self.open_path(json_path)

    def check_step1(self):
        pdf_path = self.t1_pdf_path.get()
        json_path = os.path.splitext(pdf_path)[0] + ".json"
        self.open_path(json_path)

    # --- TAB 2 ---
    def setup_tab2(self):
        self.t2_json_path = self.add_ui_row(self.tabs['tab2'], "File JSON Input:", 0)
        self.t2_book_code = self.add_ui_row(self.tabs['tab2'], "Mã Sách:", 1, is_file=False)
        self.t2_book_name = self.add_ui_row(self.tabs['tab2'], "Tên Sách:", 2, is_file=False)
        btn_frame = tk.Frame(self.tabs['tab2'])
        btn_frame.grid(column=1, row=3, pady=20)
        tk.Button(btn_frame, text="▶ TẠO EXCEL", bg="#90EE90", command=self.run_step2).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="👁 MỞ EXCEL", bg="#FFD700", command=self.check_step2).pack(side=tk.LEFT, padx=10)

    def run_step2(self):
        json_path = self.t2_json_path.get()
        code = self.t2_book_code.get()
        name = self.t2_book_name.get()
        out_path = os.path.join(os.path.dirname(json_path), f"{code}.xlsx")
        def task():
            try:
                create_excel_like_sample(json_path, code, name, out_path)
                messagebox.showinfo("Xong", f"Đã tạo: {out_path}")
            except Exception as e: messagebox.showerror("Lỗi", str(e))
        threading.Thread(target=task).start()

    def check_step2(self):
        json_path = self.t2_json_path.get()
        code = self.t2_book_code.get()
        out_path = os.path.join(os.path.dirname(json_path), f"{code}.xlsx")
        self.open_path(out_path)

    # --- TAB 3 ---
    def setup_tab3(self):
        self.t3_sgk = self.add_ui_row(self.tabs['tab3'], "File JSON SGK (Chuẩn):", 0)
        
        tk.Label(self.tabs['tab3'], text="File PDF SGV:", font=('Arial', 9, 'bold')).grid(column=0, row=1, padx=10, pady=10, sticky='W')
        self.t3_sgv_pdf = tk.StringVar()
        tk.Entry(self.tabs['tab3'], width=55, textvariable=self.t3_sgv_pdf).grid(column=1, row=1, padx=10)
        tk.Button(self.tabs['tab3'], text="📂 Chọn", command=lambda: self.browse_file(self.t3_sgv_pdf)).grid(column=2, row=1, padx=5)
        tk.Button(self.tabs['tab3'], text="👁 Check SGV", bg="#FFD700", command=lambda: self.check_json_result(self.t3_sgv_pdf.get(), "_SGV")).grid(column=3, row=1, padx=5)

        tk.Label(self.tabs['tab3'], text="File PDF SBT:", font=('Arial', 9, 'bold')).grid(column=0, row=2, padx=10, pady=10, sticky='W')
        self.t3_sbt_pdf = tk.StringVar()
        tk.Entry(self.tabs['tab3'], width=55, textvariable=self.t3_sbt_pdf).grid(column=1, row=2, padx=10)
        tk.Button(self.tabs['tab3'], text="📂 Chọn", command=lambda: self.browse_file(self.t3_sbt_pdf)).grid(column=2, row=2, padx=5)
        tk.Button(self.tabs['tab3'], text="👁 Check SBT", bg="#FFD700", command=lambda: self.check_json_result(self.t3_sbt_pdf.get(), "_SBT")).grid(column=3, row=2, padx=5)

        btn_frame = tk.Frame(self.tabs['tab3'])
        btn_frame.grid(column=1, row=3, pady=20)
        tk.Button(btn_frame, text="▶ 1. CHẠY ĐỒNG BỘ", bg="#90EE90", command=self.run_step3).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="🛠 2. AUTO FIX LOGIC", bg="#FFA07A", command=self.run_fix_tab3).pack(side=tk.LEFT, padx=10)

    def check_json_result(self, pdf_path, suffix):
        if not pdf_path: return
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        json_out_path = os.path.join(os.path.dirname(pdf_path), f"{base_name}{suffix}.json")
        if os.path.exists(json_out_path): self.open_path(json_out_path)
        else: messagebox.showwarning("Chưa có", "Chưa tìm thấy file output.")

    def run_step3(self):
        sgk, sgv, sbt = self.t3_sgk.get(), self.t3_sgv_pdf.get(), self.t3_sbt_pdf.get()
        if not sgk: 
            messagebox.showerror("Lỗi", "Thiếu JSON SGK.")
            return
        def task():
            try:
                res = []
                if sgv and os.path.exists(sgv): 
                    sync_book_menu(sgk, sgv, "_SGV")
                    res.append("✅ SGV: Xong")
                if sbt and os.path.exists(sbt): 
                    sync_book_menu(sgk, sbt, "_SBT")
                    res.append("✅ SBT: Xong")
                messagebox.showinfo("Hoàn tất", "\n".join(res))
            except Exception as e: messagebox.showerror("Lỗi", str(e))
        threading.Thread(target=task).start()

    def run_fix_tab3(self):
        sgv, sbt = self.t3_sgv_pdf.get(), self.t3_sbt_pdf.get()
        fixed = []
        if sgv:
            path = os.path.join(os.path.dirname(sgv), f"{os.path.splitext(os.path.basename(sgv))[0]}_SGV.json")
            if os.path.exists(path) and self.auto_fix_json_logic(path, "SGV"): fixed.append("SGV")
        if sbt:
            path = os.path.join(os.path.dirname(sbt), f"{os.path.splitext(os.path.basename(sbt))[0]}_SBT.json")
            if os.path.exists(path) and self.auto_fix_json_logic(path, "SBT"): fixed.append("SBT")
        if fixed: messagebox.showinfo("Xong", f"Đã fix: {', '.join(fixed)}")
        else: messagebox.showinfo("Info", "Không tìm thấy file hoặc logic đã chuẩn.")

    # --- TAB 4 ---
    def setup_tab4(self):
        self.t4_pdf = self.add_ui_row(self.tabs['tab4'], "File PDF Gốc:", 0)
        self.t4_json = self.add_ui_row(self.tabs['tab4'], "File JSON:", 1)
        self.t4_out = self.add_ui_row(self.tabs['tab4'], "Folder Output:", 2, is_file=False)
        btn_frame = tk.Frame(self.tabs['tab4'])
        btn_frame.grid(column=1, row=3, pady=20)
        tk.Button(btn_frame, text="▶ CẮT PDF", bg="#90EE90", command=self.run_step4).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="👁 KIỂM TRA", bg="#FFD700", command=self.check_step4).pack(side=tk.LEFT, padx=10)

    def run_step4(self):
        def task():
            try:
                processed_json, book_out_dir = process_lesson_tree(self.t4_pdf.get(), self.t4_json.get(), self.t4_out.get())
                cut_pdf_from_flat_json(self.t4_pdf.get(), processed_json, book_out_dir)
                messagebox.showinfo("Xong", "Đã cắt file.")
            except Exception as e: messagebox.showerror("Lỗi", str(e))
        threading.Thread(target=task).start()

    def check_step4(self):
        out_root = self.t4_out.get()
        pdf_name = os.path.splitext(os.path.basename(self.t4_pdf.get()))[0]
        self.open_path(os.path.join(out_root, pdf_name))

    # --- TAB 5: SMART RENAME ---
    def setup_tab5(self):
        self.t5_dir = self.add_ui_row(self.tabs['tab5'], "Folder (KetQua_Final):", 0, is_file=False)
        self.t5_code = self.add_ui_row(self.tabs['tab5'], "Mã Sách Mới:", 1, is_file=False)
        self.t5_sgk_json = self.add_ui_row(self.tabs['tab5'], "JSON SGK Gốc:", 2)
        
        btn_frame = tk.Frame(self.tabs['tab5'])
        btn_frame.grid(column=1, row=3, pady=20)
        
        # Chỉ cần gọi hàm, logic nằm trong finalizebook.py
        tk.Button(btn_frame, text="▶ ĐỔI TÊN & TỔNG HỢP", bg="#90EE90", command=self.run_step5).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="👁 MỞ FOLDER", bg="#FFD700", command=self.check_step5).pack(side=tk.LEFT, padx=10)

    def run_step5(self):
        work_dir = self.t5_dir.get()
        code = self.t5_code.get()
        json_sgk = self.t5_sgk_json.get()
        
        if not os.path.exists(work_dir):
            messagebox.showerror("Lỗi", "Không tìm thấy thư mục làm việc.")
            return

        def task():
            try:
                # Main Tool chỉ việc gọi, mọi logic thông minh nằm ở finalizebook.py
                finalize_project(work_dir, code, json_sgk)
                messagebox.showinfo("Thành công", "Đã đổi tên và tạo Excel tổng hợp.")
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))
        threading.Thread(target=task).start()

    def check_step5(self): 
        self.open_path(self.t5_dir.get())

    # --- TAB 6 ---
    def setup_tab6(self):
        self.t6_folder = self.add_ui_row(self.tabs['tab6'], "Folder PDF Con:", 0, is_file=False)
        btn_frame = tk.Frame(self.tabs['tab6'])
        btn_frame.grid(column=1, row=1, pady=10)
        tk.Button(btn_frame, text="▶ TẠO MARKDOWN", bg="#90EE90", command=self.run_step6).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="👁 KIỂM TRA", bg="#FFD700", command=self.check_step6).pack(side=tk.LEFT, padx=10)
        self.t6_log = tk.Text(self.tabs['tab6'], height=15, width=90)
        self.t6_log.grid(column=0, row=2, columnspan=3, padx=10, pady=10)

    def run_step6(self):
        folder = self.t6_folder.get()
        failed_log = os.path.join(os.path.dirname(folder), "FailedFile.txt")
        def task():
            self.t6_log.insert(tk.END, "Bắt đầu...\n")
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        try:
                            pdfToMdAI_Convert(os.path.splitext(f)[0], os.path.join(root, f), os.path.join(os.path.dirname(folder), "SDT_Done", os.path.basename(root)), failed_log)
                            self.t6_log.insert(tk.END, f"✅ {f}\n")
                        except Exception as e: self.t6_log.insert(tk.END, f"❌ {f}: {e}\n")
            messagebox.showinfo("Xong", "Hoàn tất.")
        threading.Thread(target=task).start()

    def check_step6(self):
        folder = self.t6_folder.get()
        self.open_path(os.path.join(os.path.dirname(folder), "SDT_Done"))

if __name__ == "__main__":
    root = tk.Tk()
    app = SachDienTuManager(root)
    root.mainloop()