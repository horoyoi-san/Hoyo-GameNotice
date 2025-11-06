from re import sub, split
from datetime import datetime
from html import unescape as unhtmlescape


def unix_time(time_val):
    if isinstance(time_val, int):
        return time_val
    elif isinstance(time_val, str):
        try:
            dt = datetime.strptime(time_val, '%Y-%m-%d %H:%M:%S')
            return int(dt.timestamp())
        except Exception:
            return 0
    return 0



def flatten(_list: list):
    result = []
    for i in _list:
        if isinstance(i, dict) and "list" in i:
            result.extend(i["list"])
        else:
            result.append(i)
    return result



def find(_list: list, func):
    return next(filter(func, _list), None)


def splitbylength(text: str, length: int):
    s = split(r'(.+?[！。\n])', text)
    _list = []
    _t = ""
    if len(text) < 1024:
        return [text]
    else:
        for i in list(range(len(s))):
            if len(_t) + len(s[i]) > length:
                _list.append(_t)
                _t = ""
            _t += s[i]
        if _t:
            _list.append(_t)
        return _list


def embUrl(text: str):
    # embed url
    return sub(r'<a href=".*?\(\'(.+?)\'\);"\s*.*?>(.+?)</a>', "\n\n[\\2](\\1)\n", text)


def removeTTag(text: str):
    # embed url
    return sub(r'</*t.*?>', "", text)
