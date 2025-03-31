import os
from telegram import Bot
from environs import Env


env = Env()
env.read_env()

TG_BOT_TOKEN = env.str("TG_BOT_TOKEN")
COURIER_CHAT_ID = env.str("COURIER_CHAT_ID")
FLORIST_CHAT_ID = env.str("FLORIST_CHAT_ID")


def send_consultation_notification(client_id):
    from flowers.models import Client
    client = Client.objects.get(id=client_id)

    message = (
        "📞 Новая заявка на консультацию!\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Имя*: {client.name}\n"
        f"📱 *Телефон*: {client.phone}\n"
    )

    if client.quiz_occasion and client.quiz_price_range:
        price_ranges = {
            'low': 'До 1 000 руб',
            'medium': '1 000 - 5 000 руб',
            'high': 'От 5 000 руб',
            'any': 'Не имеет значения'
        }
        message += (
            f"🎯 *Выбранный повод*: {client.quiz_occasion.name}\n"
            f"💰 *Выбранный бюджет*: {price_ranges.get(client.quiz_price_range, client.quiz_price_range)}\n"
        )

    message += f"🕒 *Время заявки*: {client.created_at.strftime('%d.%m.%Y %H:%M')}"

    bot = Bot(token=TG_BOT_TOKEN)
    bot.send_message(
        chat_id=FLORIST_CHAT_ID,
        text=message,
        parse_mode='Markdown',
    )


def send_delivery_notification(order_id):
    from flowers.models import Order
    order = Order.objects.get(id=order_id)

    bouquet_info = f"💐 *Букет*: {order.bouquet.name}\n💰 *Цена*: {order.bouquet.price} руб\n" if order.bouquet else ""

    message = (
        "💐 *Новый заказ!*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Клиент*: {order.client.name}\n"
        f"📱 *Телефон*: {order.client.phone}\n"
        f"🏠 *Адрес*: {order.address}\n"
        f"⏰ *Время доставки*: {order.get_delivery_time_display()}\n"
        f"{bouquet_info}"
        f"📅 *Дата заказа*: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )

    bot = Bot(token=TG_BOT_TOKEN)
    bot.send_message(
        chat_id=COURIER_CHAT_ID,
        text=message,
        parse_mode='Markdown',
    )
