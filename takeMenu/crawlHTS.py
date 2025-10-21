import requests
import json, os

def getBookMenu(url):
    try:
        headers = {
            "Accept": "application/json",
            "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
            "Access-Control-Allow-Origin": "https://hanhtrangso.nxbgd.vn",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vQGdtYWlsLmNvbSIsImp0aSI6ImZlOTI5YTUyLTJmNWYtNGM1My1iNDE0LTgwNzcyNWMxYWMzNiIsImVtYWlsIjoiZGVtb0BnbWFpbC5jb20iLCJ3c2lkIjoicXhvSXU5Q3pvMGM9IiwibmJmIjoxNzU4Nzc1NTEzLCJleHAiOjE3NTg3ODYzMTMsImlzcyI6Imh0dHBzOi8vbG9jYWxob3N0OjQ0MzM5IiwiYXVkIjoiZDFTakU5M3EraXVvMWpmb29pSkNZUGhzMWFQK3NFWDc2RHNTdUdVL05YQT0ifQ.zpeoYdXnozMqNuWa4FlcCGgYIpEua9WWeyK7GJQpwEE",
            "Content-Type": "application/json;",
            "Origin": "https://hanhtrangso.nxbgd.vn",
            "Referer": "https://hanhtrangso.nxbgd.vn/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

with open("dataFinal.json", "r", encoding="utf-8") as f:
    bookDatas = json.load(f)

for bookData in bookDatas:
    bookGroup = bookData['Group']
    bookType = bookData['Type']
    bookID = bookData['Id']
    bookName = bookData['Name']
    bookDN = bookData['DN']
    response = getBookMenu(f"https://apihanhtrangso.nxbgd.vn:8080/api/book/{bookID}")

    DN_part = bookDN.split('-')
    DN_final = "".join([part.upper() for part in DN_part])
    if "SACHGIAOVIEN" in DN_final:
        # DN_final = DN_final.replace("SACHGIAOVIEN", "_SGV")
        continue
    elif ("VOBAITAP" in DN_final) or ("BAITAP" in DN_final) or ("CHUYENDE" in DN_final):
        # DN_final = DN_final.replace("VOBAITAP", "").replace("BAITAP", "")
        # DN_final += "_SBT"
        continue
    file_name = f"SDT_{DN_final}_{bookGroup}"
    print(f"Đang xử lí {file_name}")
    bookData = response['data']
    bookIndexs = bookData['bookIndexs']

    bookIndexCount = 1
    bookMenu = []
    if not bookIndexs:
        continue
    for bookIndex in bookIndexs:
        bookIndex_DVKT = f"{file_name}_{bookIndexCount}"
        bookIndexCount += 1
        bookIndexChilds = bookIndex['bookIndexChilds']

        indexChildCount = 1
        indexChilds = []
        if not bookIndex:
            continue
        for i, child in enumerate(bookIndexChilds):
            childDVKT = f"{bookIndex_DVKT}_{indexChildCount}"
            indexChildCount += 1

            # startPage
            startPage = child.get('pageNo')

            # endPage: dựa vào child tiếp theo
            if i + 1 < len(bookIndexChilds):
                nextChild = bookIndexChilds[i+1]
                endPage = nextChild.get('pageNo', None)
                if endPage is not None:
                    endPage = endPage - 1
            else:
                endPage = ""
            treeChild = f"\"{childDVKT}\":\"{child.get('title')}. {child.get('name')}\""
            result = {
                "treeChild" : treeChild,
                "DVKT" : childDVKT,
                "startPage": startPage,
                "endPage": endPage
            }
            indexChilds.append(result)
        
        if bookIndex.get('title'):
            treeIndex = f"\"{bookIndex_DVKT}\":\"{bookIndex.get('title')}. {bookIndex.get('name')}\""
        else:
            treeIndex = f"\"{bookIndex_DVKT}\":\"{bookIndex.get('name')}\""
        indexInfo = {
                "treeIndex" : treeIndex,
                "indexChilds" : indexChilds
            }
        bookMenu.append(indexInfo)

    # Lưu ra file JSON
    with open(f"book/{file_name}.json", "w", encoding="utf-8") as out:
        json.dump(bookMenu, out, ensure_ascii=False, indent=4)
