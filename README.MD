<!-- @format -->

# TÀI LIỆU KỸ THUẬT: HỆ THỐNG QUẢN LÝ VÀ SỐ HÓA SÁCH ĐIỆN TỬ

## 1. TỔNG QUAN HỆ THỐNG

Dự án "Quản Lý Sách Điện Tử" là một ứng dụng Desktop được phát triển trên nền tảng Python (sử dụng thư viện giao diện Tkinter), tích hợp Google Vertex AI (Gemini 2.5 Pro / 3.1 Pro).

Mục tiêu cốt lõi của phần mềm là tự động hóa toàn bộ vòng đời xử lý và số hóa học liệu: từ việc bóc tách mục lục sách giáo khoa (SGK), đồng bộ cấu trúc sang Sách Bài Tập (SBT) và Sách Giáo Viên (SGV), cho đến việc cắt nhỏ tệp PDF theo từng bài học và trích xuất nội dung sang định dạng Markdown.

### Chi tiết Dữ liệu Đầu vào và Đầu ra

- Đầu vào (Input):
  - Tệp tin PDF Sách Giáo Khoa gốc, Sách Bài Tập, Sách Giáo Viên.
  - Các cấu hình bù trừ trang (Page Offset) do người dùng thiết lập.
- Đầu ra (Output):
  - Tệp tin JSON: Chứa cấu trúc mục lục dạng cây 3 cấp chuẩn xác.
  - Tệp tin Excel (.xlsx): Cây tri thức định dạng bậc thang.
  - Các tệp tin PDF nhỏ: Được cắt theo từng bài học và tự động đánh mã định danh hệ thống (ID).
  - Tệp tin Markdown (.md): Nội dung văn bản được bóc tách từ PDF bằng AI hoặc OCR.

- Đường link dẫn đến file cây tri thức sách điện tử: https://edmicrovn-my.sharepoint.com/:x:/g/personal/linhhd_edmicro_vn/IQA-BoLf1QAaQ6VDpxdHoTivAeVs8ndWpEbVs400lydlqMc?wdExp=TEAMS-TREATMENT&web=1

- Đường link dẫn đến file đầu ra sách điện tử (file pdf): https://edmicrovn-my.sharepoint.com/personal/phuongnm_edmicro_vn/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fphuongnm%5Fedmicro%5Fvn%2FDocuments%2FSDT&viewid=469a888c%2D0919%2D482b%2D9958%2D2b10c75ec204

- Đường link dẫn đến file đầu ra sách điện tử (file md): https://edmicrovn-my.sharepoint.com/my?id=%2Fpersonal%2Flinhhd%5Fedmicro%5Fvn%2FDocuments%2FSDT%5FMD%5FTIENGANH&viewid=71963447%2De65b%2D4cc8%2D91e3%2D45fec357a37a

---

## 2. CẤU TRÚC THƯ MỤC VÀ KIẾN TRÚC MÃ NGUỒN

### Sơ đồ cấu trúc thư mục

Dự án được tổ chức theo phân lớp chức năng rõ ràng để tối ưu hóa việc vận hành và bảo trì:

```
SachDienTu/
├── API/ # Module quản lý cấu hình và kết nối AI
│ ├── .env # Tệp cấu hình biến môi trường (Chứa khóa API Google Cloud)
│ ├── callAPI.py # Hàm gọi API tiêu chuẩn
│ └── callAPIforPDF.py # Hàm gọi API đặc thù có hỗ trợ đính kèm tệp PDF
├── CutPDF/ # Module phụ trách cắt tệp tin PDF
│ └── finalrun.py # Thuật toán tính toán Offset và cắt PDF dựa trên JSON phẳng
├── processMd/ # Module chuyển đổi PDF sang văn bản Markdown
│ ├── pdfToMd.py # Xử lý bằng OCR truyền thống (Tesseract, PyMuPDF)
│ └── pdfToMdAI.py # Xử lý bóc tách nội dung bằng AI để giữ nguyên cấu trúc toán học
├── processPDF/ # Module xử lý dữ liệu trung gian và đồng bộ hệ thống
│ ├── create.py # Tạo tệp Excel Cây Tri Thức từ dữ liệu JSON
│ ├── finalizebook.py # Logic tổng hợp, gắn tiền tố/hậu tố và gom nhóm tệp tin
│ ├── fixsbt.py # Công cụ AI chuyên dụng để sửa lỗi nhận diện mục lục SBT
│ └── sync_sgv_sbt.py # Thuật toán đồng bộ mục lục SGK sang SGV và SBT
├── takeMenu/ # Module nội suy và bóc tách mục lục gốc
│ ├── forceDeepScanAI.py # Quét cấu trúc sách tiêu chuẩn
│ └── smart_toc.py # Thuật toán cắt giảm dung lượng tối ưu cho các sách lớn (>40MB)
├── main.py # Tập tin khởi chạy chính - Nơi chứa mã nguồn giao diện (Tkinter)
├── requirements.txt # Danh sách các thư viện Python phụ thuộc cần cài đặt
└── README.MD # Tài liệu hướng dẫn kỹ thuật và kiến trúc (Tệp tin này)
```

### Phân tích chức năng Module chính

1. main.py (Core & GUI): Quản lý luồng thực thi 7 bước thông qua giao diện Tkinter. Khởi tạo các tiến trình đa luồng (threading) để ứng dụng không bị treo khi xử lý các tệp PDF lớn.
2. takeMenu: Sử dụng AI để đọc hiểu PDF và trích xuất ra JSON mục lục 3 cấp độ (Name, Lid, St, End). Các phần phụ lục như Lời nói đầu, Hướng dẫn sử dụng được loại bỏ.
3. processPDF: Đảm nhận việc đồng bộ (Map) vị trí trang của Sách Bài Tập và Sách Giáo Viên dựa trên bộ khung chuẩn của Sách Giáo Khoa, đồng thời tạo báo cáo Excel.
4. CutPDF: Làm phẳng (Flatten) cấu trúc JSON và sử dụng thư viện PyPDF2 để tách tệp PDF lớn thành hàng trăm tệp tin nhỏ.

---

## 3. LUỒNG XỬ LÝ DỮ LIỆU CHI TIẾT (WORKFLOW 7 BƯỚC)

Hệ thống hoạt động theo chu trình 7 bước tuần tự, tương ứng với 7 Tab trên giao diện:

- Giai đoạn 1: Trích xuất Mục Lục (SGK)
  - Hệ thống tiếp nhận tệp PDF SGK. Nếu dung lượng lớn, hệ thống tự động cắt 20 trang đầu tiên để tối ưu chi phí API. AI phân tích và trả về cấu trúc mục lục định dạng JSON.

- Giai đoạn 2: Khởi tạo Cây Tri Thức
  - Chuyển đổi JSON thành tệp Excel bậc thang. Hàm xử lý tự động phân tích tên tệp (Ví dụ: Tap 1, Tap 2) bằng Regex để ép kiểu Root ID, đồng thời sinh mã định danh nối tiếp (Ví dụ: SDT_TOAN_KNTT_C10_1_1_2) cho từng bài.
  - Mã môn:
    > SDT_MÃ MÔN_MÃ BỘ SÁCH_MÃ LỚP
  - Tên sách:
    > Môn học + Lớp (Lớp 1 - Lớp 10) + Bộ sách (Kết nối tri thức hoặc Chân trời sáng tạo)

- Giai đoạn 3: Đồng bộ Mục lục (SGV, SBT)
  - AI nhận khung JSON chuẩn của SGK và tệp PDF của SGV/SBT. Nhiệm vụ của AI là tìm bài tương ứng trong SGV/SBT để cập nhật số trang (Start, End). Nếu bài học không tồn tại trong SGV/SBT, AI tự động gán giá trị 0.
  - Đôi khi AI có thể tạo ra mục lục đánh số trang sai hoặc bị gán giá trị 0 ở toàn bộ bài học. Do đó cần phải check lại json, nếu sai có thể chạy lại hoặc sử dụng file fixsbt và fixsgv để sửa lại mục lục.

- Giai đoạn 4: Cắt tệp tin PDF
  - Hệ thống tính toán vị trí trang thực tế dựa trên tham số "Độ lệch trang" (Offset). Quá trình cắt tạo ra các tệp PDF riêng biệt, lấy ID hệ thống làm tên tệp tin.

- Giai đoạn 5: Đổi tên và Phân loại
  - Hệ thống quét các tệp PDF vừa cắt, tự động nhận diện đó là tài liệu SGK, SGV hay SBT để gắn hậu tố. Tự động gắn tiền tố mã sách lên đầu tệp tin và di chuyển toàn bộ vào thư mục SDT_Done.

- Giai đoạn 6: Chuyển đổi Markdown
  - Hệ thống hỗ trợ chạy hàng loạt (Folder Mode) hoặc chạy đơn lẻ (File Mode) để quét PDF sang Markdown bằng OCR hoặc AI.

- Giai đoạn 7: Bảo trì Tên tệp thủ công
  - Giao diện 2 cột văn bản cho phép người dùng kiểm tra và đổi tên tệp tin hàng loạt bằng tính năng Find & Replace.

---

## 4. CƠ CHẾ ĐỒNG BỘ VÀ XỬ LÝ CẮT PDF (LÕI KỸ THUẬT)

### 4.1 Cơ chế Đồng bộ Thông minh (Smart Map)

Hệ thống cung cấp toàn bộ JSON của SGK cho AI làm "Bộ khung". Lệnh hệ thống bắt AI tuyệt đối không được thêm/xóa bài hoặc đổi ID, mà chỉ được phép tìm và sửa 2 tham số: St (Trang bắt đầu) và End (Trang kết thúc).

### 4.2 Thuật toán Độ lệch trang (Page Offset)

Trong phần mềm, sẽ có lúc vị trí trang vật lý thường không khớp với trang in trên giấy do tệp PDF có chứa bìa hoặc lời tựa.

- Công thức tính: Offset = Trang vật lý hiển thị trên phần mềm - Số trang in trên mặt giấy.
- Áp dụng: Trong module CutPDF/finalrun.py, thuật toán cắt lấy vị trí Index của mảng theo công thức: Index = Trang in + Offset - 1.

---

## 5. HƯỚNG DẪN CÀI ĐẶT MÔI TRƯỜNG CỤC BỘ

1. Yêu cầu hệ thống:

- Python 3.10 trở lên.
- Cài đặt Tesseract OCR (bắt buộc nếu sử dụng module processMd/pdfToMd.py không qua AI). Cần cấu hình đường dẫn tesseract.exe vào biến môi trường hệ thống.

2. Cài đặt thư viện Python:
   Mở Terminal tại thư mục gốc của dự án và chạy lệnh:
   ```
   pip install -r requirements.txt
   ```

---

## 6. HƯỚNG DẪN VẬN HÀNH DÀNH

1. Khởi động phần mềm:
   Chạy lệnh từ Terminal:

   ```
   python main.py
   ```

2. Vận hành theo các bước:

- Tab 1: Chọn tệp PDF SGK và bấm "Chạy AI".
- Tab 2: Nạp JSON vừa tạo, nhập Mã Sách và Tên Sách, sau đó tạo Excel cây tri thức.
- Tab 3: Chọn tệp JSON SGK làm khung, tải lên PDF của SGV và SBT. Bấm "Chạy Đồng Bộ". Có thể dùng nút "Fix (AI)" nếu kiểm tra thấy kết quả lệch trang.
- Tab 4: Chọn PDF gốc, chọn file mục lục JSON tương ứng và chỉ định thư mục Output. Nhập chính xác Độ lệch trang (Offset 0 hoặc 1) và bấm Cắt PDF.
- Tab 5: Chọn thư mục chứa file đã cắt, nhập Mã Sách Mới và nạp JSON SGK. Bấm Đổi tên & Tổng hợp để hệ thống tạo danh mục tự động.
- Tab 6 & 7: Sử dụng tùy nhu cầu phát sinh để chuyển đổi văn bản sang Markdown hoặc sửa tên tệp tin bị lỗi chính tả hàng loạt.

---

## 7. LƯU Ý

- Quản lý Token AI: Vertex AI có giới hạn Token cho mỗi lượt gọi. Module takeMenu.smart_toc.py đã được tối ưu để chỉ cắt 20 trang đầu tiên của sách lớn (>40MB) gửi đi. Không nên vô hiệu hóa cơ chế này để tránh lỗi quá tải.
- Quản lý Luồng (Threading): Các tác vụ trong main.py đều sử dụng threading.Thread để giao diện Tkinter không bị đơ. Tuy nhiên, tuyệt đối không được phép thao tác trực tiếp với các Widget của Tkinter bên trong thread phụ nếu không có cơ chế đồng bộ, để tránh lỗi crash phần mềm.
- Bảo vệ dữ liệu tại Tab 7: Tính năng thay thế tên hàng loạt ở Tab 7 lấy số dòng văn bản làm chuẩn để ánh xạ với đường dẫn tệp thực tế. Cần đảm bảo người dùng không ấn phím Enter vô tình làm lệch số dòng.
