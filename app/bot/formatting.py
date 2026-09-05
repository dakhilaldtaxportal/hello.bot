def order_text(order, vendor_name, vendor_phone):
    return (
        f"📦 Order #{order.id}\n"
        f"🏪 Vendor: {vendor_name}\n"
        f"📞 Vendor phone: {vendor_phone or 'N/A'}\n"
        f"👤 Customer: {order.customer_name}\n"
        f"📞 Customer phone: {order.customer_phone or 'N/A'}\n"
        f"🗺 Customer map: {order.customer_map_url or 'Location attached'}\n"
        f"📏 Road distance: {order.road_distance_km or 0:.2f} km\n"
        f"💰 Delivery charge: {order.delivery_charge or 0:.2f} TK\n"
        f"📝 Notes: {order.notes or '-'}"
    )
