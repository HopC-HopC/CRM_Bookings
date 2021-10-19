# from flask_googlemaps import get_address, get_coordinates
from googlemaps import Client as GoogleMaps

API_KEY = "AIzaSyDbYrFwu-5Nftk1f2xc_lBZkMFSR98YGps"

gmaps = GoogleMaps(key=API_KEY)

#Geocoding: getting coordinates from address text
print(gmaps.geocode('57 Stafford Street, Norwich, NR2 3BD, United Kingdom'))