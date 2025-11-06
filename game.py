import re
from requests import get
from markdownify import markdownify as md
import util
import data

header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/119.0.0.0 Safari/537.36",
}

def convert_js_link(text: str) -> str:
    pattern = r"javascript:miHoYoGameJSSDK\.openInBrowser\('([^']+)',.*?\)"
    return re.sub(pattern, r"\1", text)

async def game(settings) -> tuple[bool, list[dict]]:
    name = settings["name"]
    lang = settings["language"]
    repo = settings["repo"]

    # ================= getAnnList =================
    url = f'https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnList?game=hk4e&game_biz=hk4e_global&lang={lang}&bundle_id=hk4e_global&level=60&platform=pc&region=os_usa&uid=1'
    response = get(url, headers=header)
    if not response:
        print(f'{name} failed.')
        return False, []
    list_obj = response.json()

    ann_list = sorted(util.flatten(list_obj["data"]["list"]),
                      key=lambda x: util.unix_time(x["start_time"]),
                      reverse=True)

    ann_list = [i for i in ann_list if not data.hasAnn(i)]
    if not ann_list:
        return True, []

    # ================= getAnnContent =================
    url = f'https://sg-hk4e-api-static.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent?game=hk4e&game_biz=hk4e_global&lang={lang}&bundle_id=hk4e_global&platform=pc&region=os_asia&level=1'
    response = get(url, headers=header)
    if not response:
        print(f'{name} failed (content).')
        return False, []
    content_obj = response.json()
    content_list = content_obj["data"]["list"]

    contents = []
    added_list = []

    # ================= process announcements =================
    for ann in ann_list:
        print(f'new announcement {ann["ann_id"]} found. {ann["title"]}')
        ann_content = util.find(content_list, lambda x: x["title"] == ann["title"])
        if not ann_content:
            print("No content match.")
            continue

        data.update(ann["ann_id"], ann_content)
        added_list.append(f'[{ann_content["title"]}](log/{ann["ann_id"]}.md)')

        text = util.embUrl(ann_content["content"])
        text = convert_js_link(text)
        text = md(text, heading_style="ATX")
        text = util.removeTTag(text).strip()

        # ================= แยกหัวข้อย่อยเหมือน SR =================
        sections = re.split(r'\n#{1,2} ', text)
        sections = [s.strip() for s in sections if s.strip()]

        for sec in sections:
            # หัวข้อ
            title_match = re.match(r'^(.*?)\n', sec)
            title = title_match.group(1).strip() if title_match else ann_content["title"]

            # ดึงภาพทั้งหมดในส่วนนี้
            imgs = re.findall(r'!\[.*?\]\((.*?)\)', sec)
            sec_text = re.sub(r'!\[.*?\]\(.*?\)', '', sec).strip()

            # ถ้าเนื้อหาเริ่มด้วยชื่อเรื่องให้ตัดออก
            if sec_text.startswith(title):
                sec_text = sec_text[len(title):].strip()

            # แบ่งข้อความยาว ๆ
            sec_split = util.splitbylength(sec_text, 1000)

            # สร้าง embed สำหรับข้อความ
            text_embed = {
                "color": 0x38A1DB,
                "title": title,
                "timestamp": ann.get("start_time"),
                "fields": [],
            }

            for part in sec_split[:3]:
                text_embed["fields"].append({"name": "", "value": part})
            if len(sec_split) > 3:
                text_embed["fields"].append({
                    "name": "",
                    "value": f'[see more...](https://github.com/{repo}/tree/main/log/{ann["ann_id"]}.md)'
                })

            contents.append({
                "username": f'{name} No.{ann["ann_id"]}',
                "embeds": [text_embed]
            })

            # เพิ่ม embed สำหรับภาพแต่ละภาพ
            for img_url in imgs:
                contents.append({
                    "username": f'{name} No.{ann["ann_id"]}',
                    "embeds": [{
                        "color": 0x38A1DB,
                        "image": {"url": img_url}
                    }]
                })

    # ================= update README.md =================
    if added_list:
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
        announcements = "  \n".join(added_list)
        readme = re.sub(
            r'## Recent Announcements\n*[\s\S]*?\n*<end>',
            f'## Recent Announcements\n{announcements}\n<end>',
            readme
        )
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme)

    return True, contents[::-1]
