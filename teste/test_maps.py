from app.services.maps import parse_coordinates

def test_coordinate_link():
    assert parse_coordinates("https://maps.google.com/?q=23.8103,90.4125") == (23.8103, 90.4125)

def test_invalid():
    assert parse_coordinates("hello") is None
