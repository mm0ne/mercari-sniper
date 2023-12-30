from discord.ext import tasks, commands
from discord import Embed
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from db.client import create_client
from utils.helper import item_already_exists, construct_url
from utils.driver import scrape
from typing import Sequence
import os
import time
import utils.constant as uc

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_CD = os.getenv("SUPABASE_TABLE_CD")
SUPABASE_TABLE_BOOK = os.getenv("SUPABASE_TABLE_BOOK")
SUPABASE_TABLE_MERCH = os.getenv("SUPABASE_TABLE_MERCH")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
INFO_CHANNEL_ID = int(os.getenv("INFO_CHANNEL_ID"))
BOOK_CHANNEL_ID = int(os.getenv("BOOK_CHANNEL_ID"))
CD_CHANNEL_ID = int(os.getenv("CD_CHANNEL_ID"))
MERCH_CHANNEL_ID = int(os.getenv("MERCH_CHANNEL_ID"))
BOOK_KEYWORDS = os.getenv("BOOK_KEYWORDS")
CD_KEYWORDS = os.getenv("CD_KEYWORDS")
CD_AND_BOOK_CATEGORY_ID = os.getenv("CD_AND_BOOK_CATEGORY_ID")
MERCH_CATEGORY_ID = os.getenv("MERCH_CATEGORY_ID")
CD_KEYWORDS = CD_KEYWORDS.split(",")
BOOK_KEYWORDS = BOOK_KEYWORDS.split(",")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")


bot = commands.Bot(command_prefix="!")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


async def start_scrape_info(keywords: Sequence[str]) -> None:
    info_channel = bot.get_channel(INFO_CHANNEL_ID)

    msg_template = ""
    for key in keywords:
        msg_template += f"\n- {key}"

    await info_channel.send(f"Scraping with keywords : {msg_template}\n")


async def end_scrape_info(duration: int) -> None:
    info_channel = bot.get_channel(INFO_CHANNEL_ID)
    await info_channel.send(f"Scraping done in  : {duration} seconds")


def parse_new_data(soup: BeautifulSoup.__class__, table_name: str, keyword_id: int) -> Sequence[dict]:
    # Extract the data you need
    item_data = soup.find_all("li", class_=uc.LI_CLASS)
    item_data = item_data[::-1]
    wrangled_data = []
    old_data = get_old_data_by_keyword_id(table_name, keyword_id)

    for item in item_data:
        product_link = item.find("a", class_=uc.PRODUCT_LINK_CLASS)
        product_link = uc.WEBSITE_URL + product_link.get("href", "#")

        if product_link is None or item_already_exists(product_link, old_data):
            continue
        product_name = item.find("span", class_=uc.ITEM_NAME_CLASS).text
        product_price = item.find("span", class_=uc.NUMBER_CLASS).text
        product_price = product_price.replace(",", "")
        product_price = int(product_price)
        product_image = item.find("img").get("src", "#")
        product_image = product_image.split(".jpg?")
        product_image = product_image[0] + ".jpg"
        product_status = item.find("div", class_=uc.SOLD_BANNER_CLASS)

        if product_status is None:
            data = {
                "link": product_link,
                "image": product_image,
                "name": product_name,
                "price": product_price,
                "keyword_id": keyword_id,
            }
            wrangled_data.append(data)

    return db_insert(table_name=table_name, data=wrangled_data)


def get_old_data_by_keyword_id(table_name: str, keyword_id: int) -> Sequence[dict]:
    response = (
        supabase.table(table_name)
        .select("*")
        .eq("keyword_id", keyword_id)
        .order("id", desc=True)
        .limit(uc.QUERY_LIMIT)
        .execute()
    )
    data = response.data
    return data


def db_insert(table_name: str, data: Sequence[dict]) -> Sequence[dict] or None:
    response = supabase.table(table_name).insert(data).execute()
    response_data = response.data
    if len(response_data) > 0:
        return response_data  # Returns the inserted/updated data
    else:
        return None


async def notify_new_item(channel_id: int, items: Sequence[dict]) -> None:
    channel = bot.get_channel(channel_id)
    if channel is not None:
        for item in items:
            name = item.get("name", "")
            price = item.get("price", "")
            link = item.get("link", "")
            image = item.get("image", "")

            user_mention = f"<@{USER_ID}>"  # Mention the user

            embed = Embed(title=name, description=f"**Price**: **¥{price}**\n**URL**: {link}")
            embed.set_image(url=image)  # Set the image URL

            await channel.send(f"{user_mention} **New item!!**", embed=embed)


async def scrape_and_notify(
    keywords: list[str],
    categories: list[str],
    table_name: list[str],
    channel_ids: list[int],
) -> None:
    for i, key in enumerate(keywords):
        if len(categories) > 0:
            for j, category in enumerate(categories):
                url_payload = construct_url(key, category)
                print(f"\nscraping with '{url_payload}' as payload\n")
                driver = scrape(url_payload)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                driver.quit()
                data = parse_new_data(soup, table_name[j], i)
                await notify_new_item(channel_id=channel_ids[j], items=data)
        else:
            url_payload = construct_url(key, None)
            print(f"\nscraping with '{url_payload}' as payload\n")
            driver = scrape(url_payload)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()
            data = parse_new_data(soup, table_name[0], i)
            await notify_new_item(channel_id=channel_ids[0], items=data)


@tasks.loop(minutes=30)  # Run every 15 minutes
async def snipe():
    # Initialize headless browser
    print("\n=========================  Sniping! =========================\n")

    await start_scrape_info(BOOK_KEYWORDS)
    start_time = time.time()

    await scrape_and_notify(
        BOOK_KEYWORDS,
        [CD_AND_BOOK_CATEGORY_ID],
        [SUPABASE_TABLE_BOOK],
        [BOOK_CHANNEL_ID],
    )

    end_time = time.time()
    await end_scrape_info(end_time - start_time)

    await start_scrape_info(CD_KEYWORDS)
    start_time = time.time()
    await scrape_and_notify(
        CD_KEYWORDS,
        [CD_AND_BOOK_CATEGORY_ID, MERCH_CATEGORY_ID],
        [SUPABASE_TABLE_CD, SUPABASE_TABLE_MERCH],
        [CD_CHANNEL_ID, MERCH_CHANNEL_ID],
    )
    end_time = time.time()
    await end_scrape_info(end_time - start_time)


@bot.event
async def on_ready():
    print(f"\n\n\nLogged in as {bot.user.name}")
    snipe.start()


bot.run(DISCORD_BOT_TOKEN)
