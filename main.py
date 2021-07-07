# blago
# Return climbing, camping, or swimming destinations with fine weather

import pyowm
from datetime import timedelta, datetime
import pandas as pd

class color:
  # more easily change the color of strings

    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class Destination:
  # recreational destinations: containing location, weather and driving details

  instances = []

  def __init__(self, apikey, name, latitude, longitude, driving_minutes=None, camping=False, climbing=False, swimming=False):
    self.apikey = apikey
    self.name = name
    self.latitude = latitude
    self.longitude = longitude
    self.driving_minutes = driving_minutes
    self.camping = camping
    self.climbing = climbing
    self.swimming = swimming
    self.df = None
    self._moderate_rain = False
    self._light_rain = False
    Destination.instances.append(self)

  def __repr__(self):
    return self.name

  def gen_weather(self, forecast_type='forecast_hourly'):
    self.forecast_type = forecast_type

    owm = pyowm.OWM(self.apikey)
    mgr = owm.weather_manager()

    # generate weather object/s according to forecast type
    one_call = mgr.one_call(lat=self.latitude,lon=self.longitude)
    if self.forecast_type == 'forecast_hourly':
      self.one_call = one_call.forecast_hourly
      self._forecast_hourly()
      self._gen_rain_dfs()
    elif self.forecast_type == 'forecast_daily':
      self.one_call = one_call.forecast_daily
      self._forecast_daily()
      self._gen_rain_dfs()
    elif self.forecast_type == 'current':
      self.one_call = one_call.current
      self._current_weather()

  # build DataFrame formatted for hourly forecast
  def _forecast_hourly(self):
    self.df = pd.DataFrame({
                  'Date' : i.reference_time(timeformat='date').date().strftime('%m-%d-%Y'),
                  'Time' : i.reference_time(timeformat='date').time().strftime('%H:%M'),
                  'Rain %' : round(i.to_dict()['precipitation_probability']*100),
                  'Temp' : round(i.temperature(unit='fahrenheit')['temp']),
                  'Status' : i.to_dict()['status'],
                  'Wind Speed' : round(i.wind(unit='miles_hour')['speed']),
                  'Wind Gusts' : round(i.wind(unit='miles_hour')['gust'])
                  } for i in self.one_call).set_index(keys=['Date', 'Time'])
    self.min_temp = self.df.Temp.min()
    self.max_temp = self.df.Temp.max()
    self.min_wind_speed = self.df['Wind Speed'].min()
    self.max_wind_speed = self.df['Wind Speed'].max()
    self.min_wind_gusts = self.df['Wind Gusts'].min()
    self.max_wind_gusts = self.df['Wind Gusts'].max()

  # build DataFrame formatted for daily forecast
  def _forecast_daily(self):
    self.df = pd.DataFrame({
                  'Date' : i.reference_time(timeformat='date').date().strftime('%m-%d-%Y'),
                  'Time' : i.reference_time(timeformat='date').time().strftime('%H:%M'),
                  'Rain %' : round(i.to_dict()['precipitation_probability']*100),
                  'Max Temp' : round(i.temperature(unit='fahrenheit')['max']),
                  'Min Temp' : round(i.temperature(unit='fahrenheit')['min']),
                  'Status' : i.to_dict()['status'],
                  'Wind Speed' : round(i.wind(unit='miles_hour')['speed']),
                  'Wind Gusts' : round(i.wind(unit='miles_hour')['gust'])
                  } for i in self.one_call).set_index(['Date', 'Time'])
    self.min_temp = self.df['Min Temp'].min()
    self.max_temp = self.df['Max Temp'].max()
    self.min_wind_speed = self.df['Wind Speed'].min()
    self.max_wind_speed = self.df['Wind Speed'].max()
    self.min_wind_gusts = self.df['Wind Gusts'].min()
    self.max_wind_gusts = self.df['Wind Gusts'].max()

  # build DataFrame formatted for current weather
  def _current_weather(self):
    self.df = pd.DataFrame({
                  'Date' : self.one_call.reference_time(timeformat='date').date().strftime('%m-%d-%Y'),
                  'Time' : self.one_call.reference_time(timeformat='date').time().strftime('%H:%M'),
                  'Temp' : round(self.one_call.temperature(unit='fahrenheit')['temp']),
                  'Status' : self.one_call.status,
                  'Status++' : self.one_call.detailed_status
                  }, index=['Date']).set_index(['Date'])

    # if currently raining, add rainfall to DataFrame
    if self.one_call.rain:
      self.df['Rainfall'] = self.one_call.rain
      self.rain = self.df['Rainfall']

    # if currently windy, add wind speed and wind gust speed to DataFrame
    if 'speed' in self.one_call.wind(unit='miles_hour').keys():
      self.df['Wind Speed'] = round(self.one_call.wind(unit='miles_hour')['speed'])
      self.wind_speed = self.df['Wind Speed']

    if 'gust' in self.one_call.wind(unit='miles_hour').keys():
      self.df['Wind Gusts'] = round(self.one_call.wind(unit='miles_hour')['gust'])
      self.wind_gusts = self.df['Wind Gusts']

    self.temp = self.df.Temp

  # build 'rain' DataFrames using boolean switches
  def _gen_rain_dfs(self):
    for val in self.df['Rain %'].values:
      if val >= 25:
        self._moderate_rain = True
      elif val >= 10:
        self._light_rain = True

    if self._light_rain == True:
      self._gen_light_rain()

    if self._moderate_rain == True:
      self._gen_moderate_rain()

  # build DataFrame of dates/times when rain probability is >= 25%
  def _gen_moderate_rain(self):
    self.rain_over_25 = pd.DataFrame({'Date' : i[0], 'Time' : i[1], 'Rain %' : self.df['Rain %'][i]} \
                            for i in self.df['Rain %'].index \
                            if self.df['Rain %'][i] >= 25).set_index('Date')
    self._gen_rain_status()

  # build DataFrame of dates/times when rain probability is >= 10% and < 25%
  def _gen_light_rain(self):
    self.rain_over_10 = pd.DataFrame({'Date' : i[0], 'Time' : i[1], 'Rain %' : self.df['Rain %'][i]} \
                            for i in self.df['Rain %'].index \
                            if (self.df['Rain %'][i] >= 10 and self.df['Rain %'][i] < 25)).set_index('Date')
    self._gen_rain_status()

  # build DataFrame of dates/times when expected conditions are 'rainy'
  def _gen_rain_status(self):
    self.rain_status = pd.DataFrame({'Date' : i[0], 'Time' : i[1], 'Weather' : self.df['Status'][i]} \
                            for i in self.df['Status'].index \
                            if self.df['Status'][i] == 'Rain').set_index('Date')
 
  # output various weather conditions formatted   
  def display_forecast(self):
    print("\n\t" + color.CYAN + "-"*len(self.name) + color.END)
    print(color.CYAN + "|" + color.END + color.BOLD + f"\t{self.name.upper()}" + color.END + color.CYAN + "|" + color.END)
    print("\t" + color.CYAN + "|" + "-"*len(self.name) + "|" + color.END)
    if self._moderate_rain == True:
      print(color.RED + f"Moderate rain expected:" + color.END)
      print(f"{self.rain_over_25}\n")
    else:
      print(color.GREEN + f"Moderate rain not expected\n" + color.END)
    if self._light_rain == True:
      print(color.RED + f"Light rain expected:" + color.END)
      print(f"{self.rain_over_10}\n")
      print(f"{self.rain_status}\n\n")
    else:
      print(color.GREEN + f"Light rain not expected\n" + color.END)
    print(f"\tMin temp: {self.min_temp} degrees")
    print(f"\tMax temp: {self.max_temp} degrees\n")
    print(f"\tWind speed: {self.min_wind_speed} - {self.max_wind_speed} mph")
    print(f"\tWind gusts: {self.min_wind_gusts} - {self.max_wind_gusts} mph")

  def display_current_weather(self):
    print("\n\t\t" + color.CYAN + "*"*len(self.name) + "**" + color.END)
    print(color.CYAN + "\t\t*" + color.END + color.BOLD + f"{self.name.upper()}" + color.END + color.CYAN + "*" + color.END)
    print("\t\t" + color.CYAN + "*"*len(self.name) + "**" + color.END)
    print("\n", self.df, "\n\n\n")
    


apikey = '85a42738f6dabfdc6c8bf64cbaa098f0'
# generate Destinations
Destination(apikey, 'Three Sisters', 39.6295, -105.3487, 45, False, True, False)
Destination(apikey, 'Clear Creek', 39.7410, -105.3478, 35, False, True, True)
Destination(apikey, 'Morrison', 39.6513, -105.1841, 24, False, True, False)
Destination(apikey, 'Eldorado Canyon', 39.9287, -105.2934, 45, False, True, False)
Destination(apikey, 'Flagstaff Mountain', 40.0031, -105.2986, 45, False, True, False)
Destination(apikey, 'Lions Den', 40.2260, -105.3504, 74, False, True, True)
Destination(apikey, 'Grand Lake - Stillwater Pass', 40.2144, -105.8858, 120, True, False, True)
Destination(apikey, 'Westcreek - Sheeps Nose Bouldering', 39.1397, -105.1949, 100, True, True, False)
Destination(apikey, 'Roy', 36.0563, -104.3615, 287, True, True, False)
Destination(apikey, 'Posos', 36.5425, -106.0791, 340, True, True, False)
Destination(apikey, 'Nosos', 36.4290, -106.0689, 323, True, True, False)
Destination(apikey, 'Durango', 37.3098, -107.8849, 379, True, True, True)
Destination(apikey, 'Pagosa Springs - Piedra River Boulders', 37.4304, -107.1937, 331, True, True, True)
Destination(apikey, 'Joes Valley', 39.2891, -111.1806, 400, True, True, True)
Destination(apikey, 'Grand Junction - Unaweep Canyon', 38.8267, -108.5852, 257, True, True, False)
Destination(apikey, 'Red Feather Lakes', 40.7543, -105.4822, 115, True, True, False)
Destination(apikey, 'Vedauwoo', 41.1776, -105.3594, 140, True, True, True)
Destination(apikey, 'Guanella Pass Bouldering', 39.6398, -105.7080, 69, False, True, False)
Destination(apikey, 'Guanella Pass Camping', 39.5424, -105.7454, 125, True, False, True)
Destination(apikey, 'Red Cliff', 39.5019, -106.3735, 125, True, True, True)
Destination(apikey, 'Buena Vista - Turtle Rock Campground (Downtown)', 38.8838, -106.1505, 145, True, True, True)
Destination(apikey, 'Buena Vista - Dispersed Mountain Camping', 38.7817, -106.2921, 162, True, False, True)
Destination(apikey, 'Hagerman Tunnel', 39.2513, -106.4789, 141, True, False, False)

for dest in Destination.instances:
  dest.gen_weather('current')
  dest.display_current_weather()
