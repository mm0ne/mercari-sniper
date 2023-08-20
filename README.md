# mercari-sniper


mercari-sniper is discord-integrated scraper bot to snipe certain items at fixed interval.
- Uses [selenium](https://pypi.org/project/selenium/) with beautifulsoup to scrape trough dom parsing<br>
- uses [discord.py](https://pypi.org/project/discord.py/) for discord bot integration
- Uses [supabase](https://supabase.com/) as the database, since i wanted to make the docker image and container be minimal as much as possible (gcp free-tier-able lol)<br>
- Uses [supabase-py](https://github.com/supabase-community/supabase-py) as middleware for querying to supabase

## Dependencies and Prerequisites

- chrome installed
- chromedriver with the **SAME** version as installed chrome
- docker
- supabase project

## Setting up the Discord
- create your own application bot and add it to desired server. [see this](https://www.xda-developers.com/how-to-create-discord-bot/)
- set up the roles, channel, etc as you wish
- get channel_id(s) and user_id(s)
- add those to your .env

## Running:

### docker
- create .env file in the project's root directory
```
# you can change the shm_size as needed
docker compose up --build -d
```
### Locally
- make sure `dependencies and prerequisites` are fulfilled
- identify path to the chromedriver executable / binary
- set the .env
```
python bot.py
```

## Overall To Do:
- [ ] Analyze deeper [mercari](https://jp.mercari.com) website bevahiour (dom and api calls)
- [ ] Add better handling for category
- [ ] Optimize logic for handling new item
- [ ] Optimize Dockerfile (image is still too big rn)
- [ ] Extend functionality (CRUD "keywords" dynamically through REST API)
- [ ] Document discord bot setup

## Contact
If you have any questions ( i mean it, ANY questions), bugs, or improvement regarding the scraper-bot, feel free to contact me through my social media (look at my github profile)
