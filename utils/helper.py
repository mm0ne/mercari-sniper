import utils.constant as uc
from typing import Sequence


def construct_url(keyword, category_id=None) -> str:
    if category_id is None:
        return f"{uc.WEBSITE_URL}/search?keyword={keyword}&order=desc&sort=created_time"
    else:
        return f"{uc.WEBSITE_URL}/search?keyword={keyword}&order=desc&sort=created_time&category_id={category_id}"


def item_already_exists(link: str, old_items: Sequence[dict]) -> bool:
    exists = False
    for old_item in old_items:
        if old_item.get("link", "#") == link:
            exists = True
            break
    return exists
