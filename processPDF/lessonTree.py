import json, os
import openpyxl

def process_lesson_tree(pdf_path, json_path, output_folder):
    file_name = os.path.basename(pdf_path).replace(".pdf", "")
    if not os.path.exists(os.path.join(output_folder, file_name)):
        os.makedirs(os.path.join(output_folder, file_name))

    with open(json_path, "r", encoding="utf-8") as f:
        bookDatas = json.load(f)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cay Kien Thuc"

    lessons_json = []

    def write_tree(data, row, col, parent_id=""):
        for item in data:
            Lid = item.get("Lid", "")
            # Sinh id theo dạng cha_con
            if parent_id:
                cur_id = f"{parent_id}_{Lid}"
            else:
                cur_id = f"{file_name}_{Lid}"
            Name = item.get("Name", "")
            excel_name = f"\"{cur_id}\":\"{Name}\""
            ws.cell(row=row, column=col, value=excel_name)
            next_row = row + 1
            # Nếu có Content là list, duyệt tiếp
            if "Content" in item and isinstance(item["Content"], list) and item["Content"]:
                for lesson in item["Content"]:
                    # Nếu lesson là cấp cuối (có St, End)
                    if "St" in lesson and "End" in lesson:
                        lesson_Lid = lesson.get("Lid", "")
                        lesson_id = f"{cur_id}_{lesson_Lid}"
                        lesson_Name = lesson.get("Name", "")
                        lesson_excel_name = f"\"{lesson_id}\":\"{lesson_Name}\""
                        ws.cell(row=next_row, column=col+1, value=lesson_excel_name)
                        # Thêm vào json
                        lessons_json.append({
                            "Name": lesson_Name,
                            "Lid": lesson_id,
                            "St": lesson.get("St", ""),
                            "End": lesson.get("End", "")
                        })
                        next_row += 1
                    # Nếu lesson còn lồng Content, đệ quy
                    elif "Content" in lesson and isinstance(lesson["Content"], list):
                        next_row = write_tree([lesson], next_row, col+1, cur_id)
                    else:
                        # Trường hợp lesson không có St/End và không có Content
                        lesson_Lid = lesson.get("Lid", "")
                        lesson_id = f"{cur_id}_{lesson_Lid}"
                        lesson_Name = lesson.get("Name", "")
                        lesson_excel_name = f"\"{lesson_id}\":\"{lesson_Name}\""
                        ws.cell(row=next_row, column=col+1, value=lesson_excel_name)
                        next_row += 1
                row = next_row
            else:
                # Nếu là cấp cuối cùng và có St, End
                if "St" in item and "End" in item:
                    lessons_json.append({
                        "Name": item.get("Name", ""),
                        "Lid": cur_id,
                        "St": item.get("St", ""),
                        "End": item.get("End", "")
                    })
                row += 1
        return row

    write_tree(bookDatas, 1, 1)

    excel_output = os.path.join(output_folder, file_name, f"{file_name}.xlsx")
    wb.save(excel_output)
    print(f"Đã tạo file Excel: {excel_output}")

    # Ghi file json chứa các bài học cuối cùng
    json_output = os.path.join(output_folder, file_name, f"{file_name}.json")
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(lessons_json, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo file JSON: {json_output}")

def scan_folder(folder, output_folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, f)
                json_path = os.path.join(root, f.replace(".pdf", ".json"))
                process_lesson_tree(pdf_path, json_path, output_folder)

if __name__ == "__main__":
    # listL = [
    #     "SDT_NGUVAN"
    # ]
    # folder_path = r"D:\\pdf\\SDT_NGUVAN_KNTT_C11"
    # for item in listL:
    #     folder = os.path.join(folder_path, item, f"{item}_SGK")
    #     for root, dirs, files in os.walk(folder):
    #         for d in dirs:
    #             class_folder = os.path.join(root, d)
    #             output_folder = os.path.join(folder_path, item, f"{item}_SGK đã fix", d)
    #             scan_folder(class_folder, output_folder)
    # Đường dẫn đến folder Ngữ Văn KNTT 11 của bạn
    folder_path = r"D:\\pdf\\SDT_NGUVAN_KNTT_C11" 

    # Lưu file Excel và JSON tổng ngay tại đó
    output_folder = folder_path 

    print(f"📂 Đang quét: {folder_path}")
    scan_folder(folder_path, output_folder)