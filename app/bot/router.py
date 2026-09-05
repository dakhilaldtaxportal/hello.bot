from telethon import events
from app.bot.handlers.common import start, registration
from app.bot.handlers.rider import begin_registration, handle_contact, handle_location, handle_text, go_online, go_offline, change_home, set_zone
from app.bot.handlers.vendor import post_order_start, post_order_text, post_order_location
from app.bot.handlers.admin import add_vendor_command, pricing_command, broadcast_rate, search_phone, suspend
from app.bot.handlers.order_actions import callback, release, complete

def register(client):
    client.add_event_handler(start, events.NewMessage(pattern=r"^/start$"))
    client.add_event_handler(begin_registration, events.NewMessage(pattern=r"^/registration$"))
    client.add_event_handler(change_home, events.NewMessage(pattern=r"^/change_home_address$"))
    client.add_event_handler(set_zone, events.NewMessage(pattern=r"^/zone$"))
    client.add_event_handler(go_online, events.NewMessage(pattern=r"^🟢 Go Online$"))
    client.add_event_handler(go_offline, events.NewMessage(pattern=r"^🔴 Go Offline$"))
    client.add_event_handler(post_order_start, events.NewMessage(pattern=r"^/post_order$"))
    client.add_event_handler(add_vendor_command, events.NewMessage(pattern=r"^/add_vendor(?: .*)?$"))
    client.add_event_handler(pricing_command, events.NewMessage(pattern=r"^/set_pricing(?: .*)?$"))
    client.add_event_handler(broadcast_rate, events.NewMessage(pattern=r"^/set_broadcast_rate(?: .*)?$"))
    client.add_event_handler(search_phone, events.NewMessage(pattern=r"^/search(?: .*)?$"))
    client.add_event_handler(lambda e: suspend(e, True), events.NewMessage(pattern=r"^/suspend(?: .*)?$"))
    client.add_event_handler(lambda e: suspend(e, False), events.NewMessage(pattern=r"^/unsuspend(?: .*)?$"))
    client.add_event_handler(lambda e: release(e), events.NewMessage(pattern=r"^/release_order/(\\d+)$"))
    client.add_event_handler(lambda e: complete(e), events.NewMessage(pattern=r"^/complete_order/(\\d+)$"))
    client.add_event_handler(callback, events.CallbackQuery())
    client.add_event_handler(handle_contact, events.NewMessage(func=lambda e: bool(getattr(e.message, "phone", None))))
    client.add_event_handler(handle_location, events.NewMessage(func=lambda e: bool(getattr(e.message, "geo", None))))
    client.add_event_handler(post_order_location, events.NewMessage(func=lambda e: bool(getattr(e.message, "geo", None))))
    client.add_event_handler(handle_text, events.NewMessage())
    client.add_event_handler(post_order_text, events.NewMessage())
