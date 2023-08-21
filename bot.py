from discord.ext import tasks, commands
from discord import Embed, Intents
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_CD = os.getenv("SUPABASE_TABLE_CD")
SUPABASE_TABLE_BOOK = os.getenv("SUPABASE_TABLE_BOOK")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
INFO_CHANNEL_ID=int(os.getenv("INFO_CHANNEL_ID"))
BOOK_CHANNEL_ID = int(os.getenv("BOOK_CHANNEL_ID"))
CD_CHANNEL_ID = int(os.getenv("CD_CHANNEL_ID"))
BOOK_KEYWORDS = os.getenv("BOOK_KEYWORDS")
CD_KEYWORDS = os.getenv("CD_KEYWORDS")
CD_AND_BOOK_CATEGORY_ID = os.getenv("CD_AND_BOOK_CATEGORY_ID")
CD_KEYWORDS = CD_KEYWORDS.split(",")
BOOK_KEYWORDS = BOOK_KEYWORDS.split(",")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

WEBSITE_URL = "https://jp.mercari.com"
NUMBER_CLASS = "number__6b270ca7"
ITEM_NAME_CLASS = "itemName__a6f874a2"
IMAGE_CLASS = "imageContainer__f8ddf3a2"
PRODUCT_LINK_CLASS = "sc-bb7da013-2 eFiPDm"
SOLD_BANNER_CLASS = "sticker__a6f874a2"
LI_CLASS = "sc-bb7da013-1 bATOfv"
QUERY_LIMIT = 200

# Initialize Discord Bot
bot = commands.Bot(command_prefix="!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def scrape_info(keywords) -> None:
    info_channel = bot.get_channel(INFO_CHANNEL_ID)
    info_channel.send(f"Scraping with keywords : {keywords}")


def initialize_database():
    q = supabase.table(SUPABASE_TABLE_CD).select().limit(1).execute()
    r = supabase.table(SUPABASE_TABLE_BOOK).select().limit(1).execute()
    ### current supabase-py doesn't support DDL sql for table.
    ### You have to manually create the table in public schema

    # if q['status_code'] == 404:
    #     print("\ncreating new table...")
    #     supabase.table(SUPABASE_TABLE).create([
    #         {"name": "link", "type": "text"},
    #         {"name": "image", "type": "text"},
    #         {"name": "name", "type": "text"},
    #         {"name": "price", "type": "numeric"},
    #     ])
    #     print("Successfully created new table\n")


def construct_url(keyword, category_id=None) -> str:
    if category_id is None:
        return f"{WEBSITE_URL}/search?keyword={keyword}&order=desc&sort=created_time"
    else:
        return f"{WEBSITE_URL}/search?keyword={keyword}&order=desc&sort=created_time&category_id={category_id}"


def init_web_driver() -> webdriver.Chrome.__class__:
    print(f"\nThe chromedriver binary is in : {CHROMEDRIVER_PATH}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    )
    driver = webdriver.Chrome(options=chrome_options, executable_path=CHROMEDRIVER_PATH)

    return driver


def scrape(driver, url_payload) -> None:
    driver.get(url_payload)
    # Wait until the specific <li> elements with the given class are present
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, IMAGE_CLASS)))


def parse_new_data(soup, table_name: str, keyword_id: int) -> list:
    # Extract the data you need
    item_data = soup.find_all("li", class_=LI_CLASS)
    item_names = soup.find_all("span", class_=ITEM_NAME_CLASS)
    item_data = item_data[::-1]
    item_names = item_names[::-1]
    wrangled_data = []
    old_data = get_old_data_by_keyword_id(table_name, keyword_id)

    for index, item in enumerate(item_data):
        product_link = item.find("a", class_=PRODUCT_LINK_CLASS)
        product_link = WEBSITE_URL + product_link.get("href", "#")

        if item_already_exists(product_link, old_data):
            continue

        product_name = item_names[index].text
        product_price = item.find("span", class_=NUMBER_CLASS).text
        product_price = product_price.replace(",", "")
        product_price = int(product_price)
        product_image = item.find("img").get("src", "#")
        product_image = product_image.split(".jpg?")
        product_image = product_image[0] + ".jpg"
        product_status = item.find("div", class_=SOLD_BANNER_CLASS)

        if product_status is None:
            data = add_new_data_to_database(
                table_name,
                product_link,
                product_image,
                product_name,
                product_price,
                keyword_id,
            )
            wrangled_data.append(data)

    return wrangled_data


def get_old_data_by_keyword_id(table_name: str, keyword_id: int) -> list:
    response = (
        supabase.table(table_name)
        .select("*")
        .eq("keyword_id", keyword_id)
        .order("id", desc=True)
        .limit(QUERY_LIMIT)
        .execute()
    )
    data = response.data
    return data


def add_new_data_to_database(
    table_name: str, link: str, image: str, name: str, price: int, keyword_id: int
) -> dict or None:
    data = {
        "link": link,
        "image": image,
        "name": name,
        "price": price,
        "keyword_id": keyword_id,
    }

    response = supabase.table(table_name).insert(data).execute()
    response_data = response.data
    if len(response_data) > 0:
        return response_data[0]  # Returns the inserted/updated data
    else:
        return None


def item_already_exists(link, old_items) -> bool:
    exists = False
    for old_item in old_items:
        if old_item.get("link", "#") == link:
            exists = True
            break
    return exists


async def notify_new_item(channel_id, items) -> None:
    channel = bot.get_channel(channel_id)
    if channel is not None:
        for item in items:
            name = item.get("name", "")
            price = item.get("price", "")
            link = item.get("link", "")
            image = item.get("image", "")

            user_mention = f"<@{USER_ID}>"  # Mention the user

            embed = Embed(
                title=name, description=f"**Price**: **¥{price}**\n**URL**: {link}"
            )
            embed.set_image(url=image)  # Set the image URL

            await channel.send(f"{user_mention} **New item!!**", embed=embed)


@tasks.loop(minutes=15)  # Run every 30 minutes
async def snipe():
    # Initialize headless browser
    driver = init_web_driver()
    print(
        "\n=========================  browser has been set!  =========================\n"
    )

    scrape_info(BOOK_KEYWORDS)
    for index, key in enumerate(BOOK_KEYWORDS):
        # Load the website
        url_payload = construct_url(key)
        print(f"\nscraping with '{url_payload}' as payload\n")
        scrape(driver, url_payload)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        data = parse_new_data(soup, SUPABASE_TABLE_BOOK, index)
        await notify_new_item(channel_id=BOOK_CHANNEL_ID, items=data)

    scrape_info(CD_KEYWORDS)
    for index, key in enumerate(CD_KEYWORDS):
        # Load the website
        url_payload = construct_url(keyword=key, category_id=CD_AND_BOOK_CATEGORY_ID)
        print(f"\nscraping with '{url_payload}' as payload\n")
        scrape(driver, url_payload)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        data = parse_new_data(soup, SUPABASE_TABLE_CD, index)
        await notify_new_item(channel_id=CD_CHANNEL_ID, items=data)

    # close the browser
    driver.quit()


@bot.event
async def on_ready():
    print(f"\n\n\nLogged in as {bot.user.name}")
    initialize_database()  # Initialize the database on bot startup
    snipe.start()


bot.run(DISCORD_BOT_TOKEN)
