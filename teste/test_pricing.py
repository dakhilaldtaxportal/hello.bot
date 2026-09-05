from app.services.pricing import delivery_charge, broadcast_rider_pay

def test_base():
    assert delivery_charge(3) == 50

def test_extra_started_km():
    assert delivery_charge(3.1) == 70
    assert delivery_charge(4.0) == 70

def test_broadcast():
    assert broadcast_rider_pay(5, 20) == 100
