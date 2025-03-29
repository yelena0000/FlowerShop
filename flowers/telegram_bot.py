import os
from telegram import Bot
from environs import Env

from django.conf import settings


env = Env()
env.read_env()

TG_BOT_TOKEN = env.str("TG_BOT_TOKEN")
TG_CHAT_ID = env.str("TG_CHAT_ID")


def send_consultation_notification(consult_id):
    from flowers.models import Consult
    consult = Consult.objects.get(id=consult_id)
    buyer = consult.buyer_name

    message = (
        "📞 Новая заявка на консультацию! 📞\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👤 *Клиент:* {name}\n"
        "📱 *Телефон:* {phone}\n"
        "🕒 *Время заявки:* {time}\n"
    ).format(
        name=buyer.buyer_name,
        phone=buyer.buyer_phone,
        time=consult.consult_time.strftime('%d.%m.%Y в %H:%M')
    )

    bot = Bot(token=TG_BOT_TOKEN)
    bot.send_message(
        chat_id=TG_CHAT_ID,
        text=message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )