# SachDienTu - Dự án Sách điện tử

## Mục đích:
- Tạo file Cây tri thức (Excel) cho dự án Sách điện tử và cắt + chuyển dạng file pdf -> markdown theo bài học.

## Quy trình:
- Sử dụng AI tạo mục lục (json) cho từng môn lớp theo Sách giáo khoa (SGK) (Hành trang số).
- Tạo mục lục cho từng môn lớp theo Sách giáo khoa (json).
- Tạo mục lục từng môn lớp cho Sách giáo viên (SGV) và Sách bài tập (SBT) theo mục lục SGK.
- Cắt PDF theo mục lục đã tạo.
- Xử lí những môn chia tập (Tiếng việt, Toán, Ngữ văn).
- Chuyển các file PDF đã cắt thành Markdown.

## Cấu trúc:
```
📁 API — Thư mục chứa các file gọi API
├── .env                   # File cấu hình môi trường (API key, token, v.v.)
├── callAPI.py             # Gọi API chung (ví dụ gửi request đến server)
└── callAPIforPDF.py       # Gọi API dành riêng cho xử lý file PDF

📁 CutPDF — Thư mục chứa các file cắt PDF
├── cutAll.py              # Cắt toàn bộ PDF thành từng phần nhỏ
├── cutPagePdf.py          # Cắt PDF theo trang cụ thể
├── cutPDF.py              # Hàm chính cắt PDF (module trung tâm)
└── cutTap.py              # Cắt PDF theo “tập” (phần hoặc chương)

📁 processMd — Thư mục xử lý Markdown (MD)
├── pdfToMd.py             # Chuyển PDF sang Markdown Python cơ bản
├── pdfToMdAI.py           # Chuyển PDF sang Markdown có hỗ trợ AI (tự động nhận diện)
├── pdfToMdMarker.py       # Đánh dấu (highlight/marker) trong file Markdown
└── pdfToMdMp.py           # Chuyển PDF sang Markdown sử dụng MathPix

📁 processPDF — Thư mục xử lý PDF nâng cao
├── compressPDF.py         # Nén dung lượng PDF
├── fillBook.py            # Lọc sách PDF chưa được chuyển sang Markdown
├── fixLidSBT.py           # Tạo mục lục cho tài liệu SBT (sách bài tập)
├── fixLidSGV.py           # Tạo mục lục cho tài liệu SGV (sách giáo viên)
├── lessonTree.py          # Tạo mục lục (json) và cây tri thức (Excel) cho từng PDF
├── moveTap.py             # Di chuyển, gom nhóm các PDF được chia theo tập
├── rename.py              # Đổi tên file PDF
├── renameExcel.py         # Đổi tên dựa theo danh sách trong Excel
└── splitFile.py           # Lọc PDF theo từng mã môn

📁 takeMenu — Thư mục liên quan đến việc lấy dữ liệu menu hoặc danh sách
├── bookMenu.py            # Lấy danh sách menu (mục lục) sách
├── crawlHTS.py            # Crawler lấy dữ liệu từ trang Hanhtrangso
├── mergeJsonToan.py       # Nối mục lục (json) môn Toán
└── renameTap2.py          # Đổi tên các file PDF chia tập
```