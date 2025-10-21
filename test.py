import json, unicodedata

def normalize_text(s):
    if s is None:
        return ""
    return unicodedata.normalize("NFC", str(s))

allDatas = []
count = 0
for i in range(1, 13):
    with open(f"bookList{i}.json", "r", encoding="utf-8") as f:
        dt = json.load(f)
    dts = dt["data"]
    for item in dts:
        allDatas.append(item)

dataFinal = []

for data in allDatas:
    if normalize_text(data["name"]) == normalize_text("Kết nối tri thức với cuộc sống"):
        group_code = "KNTT"
    elif normalize_text(data["name"]) == normalize_text("Chân trời sáng tạo"):
        group_code = "CTST"
    else:
        continue

    # Duyệt qua các nhóm sách
    for bg in data["bookGroups"]:
        if normalize_text(bg["name"]) == normalize_text("Sách giáo khoa"):
            type_code = "SGK"
        elif normalize_text(bg["name"]) == normalize_text("Sách bổ trợ"):
            type_code = "SBT"
        elif normalize_text(bg["name"]) == normalize_text("Sách giáo viên"):
            type_code = "SGV"
        else:
            continue

        # Duyệt qua các cuốn trong nhóm
        for book in bg["books"]:
            book_data = {
                "Group": group_code,
                "Type": type_code,
                "Id": book["bookId"],
                "Name": book["name"],
                "DN": book["slug"],
            }
            dataFinal.append(book_data)
            if type_code == "SGK":
                count += 1

# Xuất ra file JSON đẹp
with open("dataFinal.json", "w", encoding="utf-8") as f:
    json.dump(dataFinal, f, ensure_ascii=False, indent=4)
print(count)