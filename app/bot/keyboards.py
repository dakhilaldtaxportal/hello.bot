from telethon import Button

def main_menu():
    return [
        [Button.text("🟢 Go Online"), Button.text("🔴 Go Offline")],
        [Button.text("📍 Change Home Address"), Button.text("📏 Zone")],
        [Button.text("📦 My Orders")],
    ]

def location_button():
    return [Button.request_location("📍 Share Current Location")]
