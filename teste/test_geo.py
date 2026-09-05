from app.services.geo import haversine_km, inside_radius

def test_same_point():
    assert haversine_km(0,0,0,0) == 0

def test_radius():
    assert inside_radius(0,0,0,0,1)
