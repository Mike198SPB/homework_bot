
# Yandex Practicum HW bot

In this study project with Yandex Practicum, Telegram bot was developed using python-telegram-bot library.


## Documentation

Yandex Practicum HW bot can:

1️⃣ Poll Practicum.Homework API every 10 minutes and check the status of the homework submitted for review.

2️⃣ When updating the status, analyze API response and send corresponding notification in Telegram.

3️⃣ Logging work and notify about important issues with a message in Telegram.


## Tech Stack

**python==3.9** 

**python-telegram-bot==13.7** 


## Run Locally (MacOS)

Clone the project

```bash
  git clone https://github.com/Mike198SPB/homework_bot.git
```

Go to the project directory

```bash
  cd homework_bot
```

Create and activate virtual environment

```bash
  python3.9 -m venv venv
  source venev/bin/activate
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Add .env with personal data and tokens

```bash
  touch .env
```


## Environment Variables

To run this project, you will need to add the following constatnts to your .env file

`PRACTICUM_TOKEN`

`TELEGRAM_TOKEN`

`TELEGRAM_CHAT_ID`


## Authors

- [@Mike198SPB](https://github.com/Mike198SPB)


## License

[MIT](https://choosealicense.com/licenses/mit/)


## Support

For support, email Mike8670@yandex.ru


