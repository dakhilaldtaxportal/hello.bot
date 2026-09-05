from math import ceil

def delivery_charge(distance_km, base_km=3, base_charge=50, extra_km_charge=20):
    if distance_km <= base_km:
        return float(base_charge)
    extra_started_km = ceil(distance_km - base_km)
    return float(base_charge + extra_started_km * extra_km_charge)

def broadcast_rider_pay(distance_km, rate_per_km):
    return round(max(0.0, distance_km) * rate_per_km, 2)
