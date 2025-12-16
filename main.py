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
    
    # IMPORT HÀM FIX SBT MỚI (DÙNG AI)
    from processPDF.fixsbt import fixBookMenuFromAI
except ImportError as e:
    print(f"⚠️ Cảnh báo thiếu file nguồn: {e}")

class SachDienTuManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản Lý Sách Điện Tử (AI Powered)")
        self.root.geometry("1000x750")

        tabControl = ttk.Notebook(root)
        self.tabs = {}
        step_names = [
            ('tab1', '1. Tạo JSON Mục Lục'),
            ('tab2', '2. Tạo Excel (Tree)'),
            ('tab3', '3. Đồng bộ & Fix AI'),
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

    # --- AUTO FIX JSON (LOGIC CŨ - DÙNG CHO TAB 1 & SGV) ---
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
            else:
                messagebox.showinfo(f"Fix {label}", "Logic (Start-End) đã chuẩn.")
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

    # --- TAB 3 (UPDATED) ---
    def setup_tab3(self):
        self.t3_sgk = self.add_ui_row(self.tabs['tab3'], "File JSON SGK (Chuẩn):", 0)

        # SGV Row
        self.t3_use_sgv = tk.IntVar(value=1)
        tk.Checkbutton(self.tabs['tab3'], text="Sách Giáo Viên (SGV)", variable=self.t3_use_sgv, font=('Arial', 9, 'bold')).grid(column=0, row=1, padx=10, pady=10, sticky='W')
        self.t3_sgv_pdf = tk.StringVar()
        tk.Entry(self.tabs['tab3'], width=50, textvariable=self.t3_sgv_pdf).grid(column=1, row=1, padx=5)
        tk.Button(self.tabs['tab3'], text="📂", command=lambda: self.browse_file(self.t3_sgv_pdf)).grid(column=2, row=1)
        
        frame_sgv = tk.Frame(self.tabs['tab3'])
        frame_sgv.grid(column=3, row=1, padx=5)
        # Nút Fix SGV vẫn dùng Logic Fix cũ (hoặc cập nhật sau nếu có file AI cho SGV)
        tk.Button(frame_sgv, text="🛠 Fix SGV (Logic)", bg="#FFA07A", command=lambda: self.run_fix_single("SGV")).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_sgv, text="👁 Check", bg="#FFD700", command=lambda: self.check_json_result(self.t3_sgv_pdf.get(), "_SGV")).pack(side=tk.LEFT, padx=2)

        # SBT Row
        self.t3_use_sbt = tk.IntVar(value=1)
        tk.Checkbutton(self.tabs['tab3'], text="Sách Bài Tập (SBT)", variable=self.t3_use_sbt, font=('Arial', 9, 'bold')).grid(column=0, row=2, padx=10, pady=10, sticky='W')
        self.t3_sbt_pdf = tk.StringVar()
        tk.Entry(self.tabs['tab3'], width=50, textvariable=self.t3_sbt_pdf).grid(column=1, row=2, padx=5)
        tk.Button(self.tabs['tab3'], text="📂", command=lambda: self.browse_file(self.t3_sbt_pdf)).grid(column=2, row=2)
        
        frame_sbt = tk.Frame(self.tabs['tab3'])
        frame_sbt.grid(column=3, row=2, padx=5)
        # Nút Fix SBT sử dụng AI (fixsbt.py)
        tk.Button(frame_sbt, text="🛠 Fix SBT (AI)", bg="#FF4500", fg="white", command=lambda: self.run_fix_single("SBT")).pack(side=tk.LEFT, padx=2)
        tk.Button(frame_sbt, text="👁 Check", bg="#FFD700", command=lambda: self.check_json_result(self.t3_sbt_pdf.get(), "_SBT")).pack(side=tk.LEFT, padx=2)

        btn_frame = tk.Frame(self.tabs['tab3'])
        btn_frame.grid(column=1, row=3, pady=20)
        tk.Button(btn_frame, text="▶ CHẠY ĐỒNG BỘ", bg="#90EE90", font=('Arial', 10, 'bold'), command=self.run_step3).pack(side=tk.LEFT, padx=10)

    def check_json_result(self, pdf_path, suffix):
        if not pdf_path: return
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        json_out_path = os.path.join(os.path.dirname(pdf_path), f"{base_name}{suffix}.json")
        if os.path.exists(json_out_path): self.open_path(json_out_path)
        else: messagebox.showwarning("Chưa có", "Chưa tìm thấy file kết quả.")

    def run_step3(self):
        use_sgv, use_sbt = self.t3_use_sgv.get(), self.t3_use_sbt.get()
        sgk, sgv_path, sbt_path = self.t3_sgk.get(), self.t3_sgv_pdf.get(), self.t3_sbt_pdf.get()

        if not sgk: 
            messagebox.showerror("Lỗi", "Thiếu JSON SGK.")
            return
        if not use_sgv and not use_sbt:
            messagebox.showwarning("Chú ý", "Bạn chưa chọn sách nào để chạy.")
            return

        def task():
            try:
                res = []
                if use_sgv:
                    if sgv_path and os.path.exists(sgv_path):
                        sync_book_menu(sgk, sgv_path, "_SGV")
                        res.append("✅ SGV: Đồng bộ xong.")
                    else: res.append("⚠️ SGV: Thiếu file PDF.")
                if use_sbt:
                    if sbt_path and os.path.exists(sbt_path):
                        sync_book_menu(sgk, sbt_path, "_SBT")
                        res.append("✅ SBT: Đồng bộ xong.")
                    else: res.append("⚠️ SBT: Thiếu file PDF.")
                messagebox.showinfo("Hoàn tất", "\n".join(res))
            except Exception as e: messagebox.showerror("Lỗi", str(e))
        threading.Thread(target=task).start()

    def run_fix_single(self, type_book):
        """
        Hàm xử lý Fix riêng lẻ.
        - Nếu type_book == "SBT": Gọi AI từ fixsbt.py
        - Nếu type_book == "SGV": Gọi Auto Logic Fix (cũ)
        """
        sgk_path = self.t3_sgk.get()
        pdf_path = ""
        
        if type_book == "SGV": 
            pdf_path = self.t3_sgv_pdf.get()
        elif type_book == "SBT": 
            pdf_path = self.t3_sbt_pdf.get()
        
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showwarning("Thiếu file", f"Chưa chọn file PDF cho {type_book}")
            return

        # --- LOGIC FIX SBT (DÙNG AI) ---
        if type_book == "SBT":
            if not sgk_path or not os.path.exists(sgk_path):
                messagebox.showerror("Thiếu file", "Cần file JSON SGK (Chuẩn) để AI đối chiếu.")
                return
            
            # Hỏi xác nhận vì AI chạy lâu/tốn tiền
            if not messagebox.askyesno("Xác nhận chạy AI", f"Bạn sắp dùng AI để fix {type_book}.\nViệc này có thể tốn một chút thời gian. Tiếp tục?"):
                return

            def task_ai_sbt():
                try:
                    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
                    output_dir = os.path.dirname(pdf_path)
                    
                    # Gọi hàm từ fixsbt.py
                    # Signature: fixBookMenuFromAI(file_name, sbt_pdf_path, sgk_json_path, output_path, model="gemini-2.5-pro")
                    fixBookMenuFromAI(file_name, pdf_path, sgk_path, output_dir)
                    
                    messagebox.showinfo("Xong", f"AI đã xử lý xong SBT.\nFile lưu tại: {output_dir}")
                except Exception as e:
                    messagebox.showerror("Lỗi AI", str(e))
            
            threading.Thread(target=task_ai_sbt).start()

        # --- LOGIC FIX SGV (DÙNG THUẬT TOÁN CŨ) ---
        else:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            json_path = os.path.join(os.path.dirname(pdf_path), f"{base_name}_{type_book}.json")
            
            if os.path.exists(json_path):
                if self.auto_fix_json_logic(json_path, type_book):
                    self.open_path(json_path)
            else:
                messagebox.showwarning("Lỗi", "Chưa tìm thấy file JSON. Hãy chạy đồng bộ trước.")

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

    # --- TAB 5 ---
    def setup_tab5(self):
        self.t5_dir = self.add_ui_row(self.tabs['tab5'], "Folder (KetQua_Final):", 0, is_file=False)
        self.t5_code = self.add_ui_row(self.tabs['tab5'], "Mã Sách Mới:", 1, is_file=False)
        self.t5_sgk_json = self.add_ui_row(self.tabs['tab5'], "JSON SGK Gốc:", 2)
        btn_frame = tk.Frame(self.tabs['tab5'])
        btn_frame.grid(column=1, row=3, pady=20)
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
                finalize_project(work_dir, code, json_sgk)
                messagebox.showinfo("Thành công", "Đã đổi tên và tạo Excel tổng hợp.")
            except Exception as e: messagebox.showerror("Lỗi", str(e))
        threading.Thread(target=task).start()

    def check_step5(self): self.open_path(self.t5_dir.get())

    # --- TAB 6 ---
    # --- TAB 6 (NÂNG CẤP: CHỌN FOLDER HOẶC 1 FILE) ---
    def setup_tab6(self):
        # 1. Chọn chế độ
        tk.Label(self.tabs['tab6'], text="Chọn chế độ xử lý:", font=('Arial', 9, 'bold')).grid(column=0, row=0, padx=10, pady=10, sticky='W')
        
        self.t6_mode = tk.StringVar(value="folder")
        
        # Radio buttons để chuyển đổi giao diện logic
        rb_frame = tk.Frame(self.tabs['tab6'])
        rb_frame.grid(column=1, row=0, sticky='W', padx=10)
        tk.Radiobutton(rb_frame, text="Quét cả Folder (Hàng loạt)", variable=self.t6_mode, value="folder", 
                       command=self.toggle_tab6_ui).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(rb_frame, text="Chạy 1 File lẻ (Sửa lỗi)", variable=self.t6_mode, value="file", 
                       command=self.toggle_tab6_ui).pack(side=tk.LEFT, padx=10)

        # 2. Input cho Folder
        self.t6_folder_label = tk.Label(self.tabs['tab6'], text="Folder chứa PDF con:")
        self.t6_folder_label.grid(column=0, row=1, padx=10, pady=10, sticky='W')
        
        self.t6_folder = tk.StringVar()
        self.t6_folder_entry = tk.Entry(self.tabs['tab6'], width=65, textvariable=self.t6_folder)
        self.t6_folder_entry.grid(column=1, row=1, padx=10, pady=10)
        self.t6_folder_btn = tk.Button(self.tabs['tab6'], text="📂 Chọn Folder", command=lambda: self.browse_directory(self.t6_folder))
        self.t6_folder_btn.grid(column=2, row=1, padx=5)

        # 3. Input cho Single File
        self.t6_file_label = tk.Label(self.tabs['tab6'], text="File PDF cần chạy lại:")
        self.t6_file_label.grid(column=0, row=2, padx=10, pady=10, sticky='W')
        
        self.t6_file = tk.StringVar()
        self.t6_file_entry = tk.Entry(self.tabs['tab6'], width=65, textvariable=self.t6_file)
        self.t6_file_entry.grid(column=1, row=2, padx=10, pady=10)
        self.t6_file_btn = tk.Button(self.tabs['tab6'], text="📂 Chọn File", command=lambda: self.browse_file(self.t6_file))
        self.t6_file_btn.grid(column=2, row=2, padx=5)

        # 4. Action Buttons
        btn_frame = tk.Frame(self.tabs['tab6'])
        btn_frame.grid(column=1, row=3, pady=20)
        tk.Button(btn_frame, text="▶ BẮT ĐẦU PROCESS (AI)", bg="#90EE90", font=('Arial', 10, 'bold'), command=self.run_step6).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="👁 KIỂM TRA KẾT QUẢ", bg="#FFD700", command=self.check_step6).pack(side=tk.LEFT, padx=10)

        # 5. Log
        self.t6_log = tk.Text(self.tabs['tab6'], height=15, width=90)
        self.t6_log.grid(column=0, row=4, columnspan=3, padx=10, pady=10)

        # Khởi chạy trạng thái UI ban đầu
        self.toggle_tab6_ui()

    def browse_directory(self, var):
        filename = filedialog.askdirectory()
        if filename: var.set(filename)

    def toggle_tab6_ui(self):
        """Ẩn hiện input dựa theo chế độ chọn"""
        mode = self.t6_mode.get()
        if mode == "folder":
            self.t6_folder_entry.config(state='normal')
            self.t6_folder_btn.config(state='normal')
            self.t6_file_entry.config(state='disabled')
            self.t6_file_btn.config(state='disabled')
        else:
            self.t6_folder_entry.config(state='disabled')
            self.t6_folder_btn.config(state='disabled')
            self.t6_file_entry.config(state='normal')
            self.t6_file_btn.config(state='normal')

    def run_step6(self):
        mode = self.t6_mode.get()
        
        # --- LOGIC 1: CHẠY CẢ FOLDER ---
        if mode == "folder":
            folder = self.t6_folder.get()
            if not folder or not os.path.exists(folder):
                messagebox.showerror("Lỗi", "Chưa chọn thư mục hợp lệ.")
                return
            
            failed_log = os.path.join(os.path.dirname(folder), "FailedFile.txt")
            
            def task_folder():
                self.t6_log.insert(tk.END, f"🚀 Bắt đầu quét folder: {os.path.basename(folder)}\n")
                for root, dirs, files in os.walk(folder):
                    for f in files:
                        if f.lower().endswith(".pdf"):
                            pdf_path = os.path.join(root, f)
                            file_name = os.path.splitext(f)[0]
                            # Output logic: ../SDT_Done/TenFolderCon
                            parent_folder_name = os.path.basename(root)
                            output_folder = os.path.join(os.path.dirname(folder), "SDT_Done", parent_folder_name)
                            
                            try:
                                self.t6_log.insert(tk.END, f"⏳ Đang xử lý: {f}...\n")
                                self.t6_log.see(tk.END)
                                pdfToMdAI_Convert(file_name, pdf_path, output_folder, failed_log)
                                self.t6_log.insert(tk.END, f"✅ Xong: {f}\n")
                            except Exception as e:
                                self.t6_log.insert(tk.END, f"❌ Lỗi {f}: {e}\n")
                self.t6_log.insert(tk.END, "🎉 HOÀN TẤT QUÁ TRÌNH FOLDER!\n")
                messagebox.showinfo("Xong", "Đã xử lý xong folder.")
            
            threading.Thread(target=task_folder).start()

        # --- LOGIC 2: CHẠY 1 FILE LẺ ---
        else:
            pdf_path = self.t6_file.get()
            if not pdf_path or not os.path.exists(pdf_path):
                messagebox.showerror("Lỗi", "Chưa chọn file PDF hợp lệ.")
                return
            
            def task_file():
                file_name = os.path.splitext(os.path.basename(pdf_path))[0]
                self.t6_log.insert(tk.END, f"🚀 Bắt đầu xử lý file lẻ: {file_name}\n")
                
                # Tính toán đường dẫn Output để khớp cấu trúc dự án
                # Giả sử file nằm ở: .../SDT_TOAN/SDT_TOAN_SGK/Bai1/1.pdf
                # Output sẽ là: .../SDT_TOAN/SDT_Done/Bai1/1.md
                
                parent_dir = os.path.dirname(pdf_path)      # Folder chứa file (Bai1)
                grandparent_dir = os.path.dirname(parent_dir) # Folder cha (SDT_TOAN_SGK) hoặc Root
                
                # Nếu cấu trúc file đúng chuẩn dự án
                folder_name = os.path.basename(parent_dir)
                
                # Tạo output folder trong SDT_Done (cùng cấp với folder chứa PDF nếu có thể, hoặc hỏi user)
                # Ở đây ta giả định cấu trúc chuẩn: Root/SDT_Code/PDF_Folder -> Root/SDT_Done/PDF_Folder
                # Để an toàn nhất, ta lùi lại 2 cấp để tìm chỗ đặt SDT_Done
                
                # Logic đơn giản hóa: Tạo folder SDT_Done ngay cạnh folder cha của file pdf
                output_base = os.path.join(os.path.dirname(parent_dir), "SDT_Done")
                output_folder = os.path.join(output_base, folder_name)
                
                failed_log = os.path.join(output_base, "FailedFile_Single.txt")

                try:
                    self.t6_log.insert(tk.END, f"📂 Output sẽ lưu tại: {output_folder}\n")
                    self.t6_log.see(tk.END)
                    
                    pdfToMdAI_Convert(file_name, pdf_path, output_folder, failed_log)
                    
                    self.t6_log.insert(tk.END, f"✅ Xong: {file_name}.md\n")
                    messagebox.showinfo("Xong", f"Đã tạo file Markdown:\n{file_name}.md")
                except Exception as e:
                    self.t6_log.insert(tk.END, f"❌ Lỗi: {e}\n")
                    messagebox.showerror("Lỗi AI", str(e))

            threading.Thread(target=task_file).start()

    def check_step6(self):
        mode = self.t6_mode.get()
        target_path = ""
        
        if mode == "folder":
            # Mở folder SDT_Done ngang cấp với folder input
            inp = self.t6_folder.get()
            if inp:
                target_path = os.path.join(os.path.dirname(inp), "SDT_Done")
        else:
            # Mở folder chứa file output của file lẻ
            inp = self.t6_file.get()
            if inp:
                parent = os.path.dirname(inp)
                target_path = os.path.join(os.path.dirname(parent), "SDT_Done", os.path.basename(parent))

        if target_path and os.path.exists(target_path):
            self.open_path(target_path)
        else:
            # Fallback: Mở folder SDT_Done chung nếu không tính toán được chính xác
            messagebox.showwarning("Thông báo", "Không tìm thấy đường dẫn chính xác, đang mở thư mục gốc...")
            if self.t6_folder.get():
                fallback = os.path.join(os.path.dirname(self.t6_folder.get()), "SDT_Done")
                if os.path.exists(fallback):
                    self.open_path(fallback)
                else:
                    messagebox.showerror("Lỗi", "Chưa có folder kết quả SDT_Done.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SachDienTuManager(root)
    root.mainloop()