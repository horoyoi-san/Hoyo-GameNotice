import re
from requests import get
from markdownify import markdownify as md
import util
import data

header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
}

def convert_js_link(text: str) -> str:
    pattern = r"javascript:miHoYoGameJSSDK\.openInBrowser\('([^']+)',.*?\)"
    return re.sub(pattern, r"\1", text)

async def game(settings) -> tuple[bool, list[dict]]:
    name = settings["name"]
    lang = settings["language"]
    repo = settings["repo"]

    url = f'https://sg-hk4e-api-static.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent?game=hk4e&game_biz=hk4e_global&lang={lang}&bundle_id=hk4e_global&platform=pc&region=os_asia&level=1'
    response = get(url, headers=header)
    if not response:
        print(f'{name} failed.')
        return False, []

    content_obj = response.json()
    raw_list = content_obj.get("data", {}).get("list", [])
    if not isinstance(raw_list, list):
        raw_list = []

    ann_list = []
    for i in raw_list:
        if isinstance(i, dict) and "list" in i:
            ann_list.extend(i["list"])
        else:
            ann_list.append(i)

    ann_list = sorted(ann_list, key=lambda x: util.unix_time(x.get("start_time", 0)), reverse=True)
    ann_list = [i for i in ann_list if not data.hasAnn(i)]
    if not ann_list:
        return True, []

    contents = []
    added_list = []

    for ann in ann_list:
        ann_content = util.find(raw_list, lambda x: x.get("title") == ann.get("title"))
        if not ann_content:
            continue

        data.update(ann.get("ann_id"), ann_content)
        added_list.append(f'[{ann_content.get("title")}](log/{ann.get("ann_id")}.md)')

        text = util.embUrl(ann_content.get("content", ""))
        text = convert_js_link(text)
        text = md(text, heading_style="ATX")
        text = util.removeTTag(text).strip()

        sections = re.split(r'\n#{1,2} ', text)
        sections = [s.strip() for s in sections if s.strip()]

        for sec in sections:
            title_match = re.match(r'^(.*?)\n', sec)
            title = title_match.group(1).strip() if title_match else ann_content.get("title")

            img_match = re.search(r'!\[.*?\]\((.*?)\)', sec)
            img_url = img_match.group(1) if img_match else ann_content.get("banner")

            sec_text = re.sub(r'!\[.*?\]\(.*?\)', '', sec).strip()
            if sec_text.startswith(title):
                sec_text = sec_text[len(title):].strip()

            sec_split = util.splitbylength(sec_text, 1000)

            embed = {
                "color": 0xF1C40F,
                "title": title,
                "timestamp": ann.get("start_time"),
                "image": {"url": img_url},
                "fields": [],
            }

            for part in sec_split[:3]:
                embed["fields"].append({"name": "", "value": part})

            if len(sec_split) > 3:
                embed["fields"].append(
                    {"name": "", "value": f'[see more...](https://github.com/{repo}/tree/main/log/{ann.get("ann_id")}.md)'}
                )

            contents.append({"username": f'{name} No.{ann.get("ann_id")}', "embeds": [embed]})

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
