# blago
# Return climbing, camping, or swimming destinations with fine weather

# class Destination:
# 	instances = []

# 	def __init__(self, destination, driving_time=None, camping=False, climbing=False, swimming=False):
# 		self.destination = destination
# 		self.driving_time = driving_time
# 		self.camping = camping
# 		self.climbing = climbing
# 		self.swimming = swimming
# 		# longitude/latitude?

# 	def __repr__(self):
# 		return self.destination

import requests

url = "https://api.tomorrow.io/v4/timelines"

querystring = {
	"location" : "60df522ea5164000088313d9",
	"units":"metric",
	"timesteps":"1h",
	"apikey":"9oLfMYMviTUc4JKyzlFTGVqkpJv8IIfU",
    "epaHealthConcern": {
      "0": "Good",
      "1": "Moderate",
      "2": "Unhealthy for Sensitive Groups",
      "3": "Unhealthy",
      "4": "Very Unhealthy",
      "5": "Hazardous"
    },
    "mepHealthConcern": {
      "0": "Good",
      "1": "Moderate",
      "2": "Unhealthy for Sensitive Groups",
      "3": "Unhealthy",
      "4": "Very Unhealthy",
      "5": "Hazardous"
    },
    "humidity": "%",
    "precipitationProbability": "%",
    "temperature": "Celcius",
    "weatherCode": {
      "0": "Unknown",
      "1000": "Clear",
      "1001": "Cloudy",
      "1100": "Mostly Clear",
      "1101": "Partly Cloudy",
      "1102": "Mostly Cloudy",
      "2000": "Fog",
      "2100": "Light Fog",
      "3000": "Light Wind",
      "3001": "Wind",
      "3002": "Strong Wind",
      "4000": "Drizzle",
      "4001": "Rain",
      "4200": "Light Rain",
      "4201": "Heavy Rain",
      "5000": "Snow",
      "5001": "Flurries",
      "5100": "Light Snow",
      "5101": "Heavy Snow",
      "6000": "Freezing Drizzle",
      "6001": "Freezing Rain",
      "6200": "Light Freezing Rain",
      "6201": "Heavy Freezing Rain",
      "7000": "Ice Pellets",
      "7101": "Heavy Ice Pellets",
      "7102": "Light Ice Pellets",
      "8000": "Thunderstorm"
    },
    "windGust": "m/s",
    "windSpeed": "mph"
}

headers = {"Accept": "application/json"}

response = requests.request("GET", url, headers=headers, params=querystring)

print(response.text)
