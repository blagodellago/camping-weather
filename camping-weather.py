# blago
# Return bouldering, camping, or swimming destinations with fine weather

import pyowm, sys, getopt, os
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import numpy as np

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
  LIGHTGREY = '\033[37m'
  DARKGREY = '\033[90m'
  BLACK = '\033[30m'
  LIGHTGREEN = '\033[92m'
  PINK = '\033[95m'

  LIGHTGREY_BG = '\033[47m'
  BLUE_BG = '\033[44m'
  GREEN_BG = '\033[42m'


class Destination:
  # recreational destinations: containing location, weather and driving details

  instances = []

  # save weather output to file
  @classmethod
  def output(cls, forecast_type):
    pwd = str(Path.cwd())
    filepath = f"{pwd}/WeatherOutput/{date.today().strftime('%m-%d-%Y')}__{forecast_type}.txt"
    if os.path.exists(filepath):
      os.remove(filepath)
    weatherFile = open(filepath, 'a')
    for dest in Destination.instances:
      if dest.active == True:
        weatherFile.write("\n\t" + color.PURPLE + "-"*len(dest.name) + color.END +\
                          color.BOLD + f"\n\t{dest.name.upper()}" + color.END +\
                          "\n\t" + color.PURPLE + "-"*len(dest.name) + color.END +\
                          f"\n- Driving minutes: {dest.driving_minutes}\
                          \n- Bouldering: {dest.bouldering}\
                          \n- Camping: {dest.camping}\
                          \n- Swimming: {dest.swimming}\n")

        if dest.forecast_type == 'current':
          weatherFile.write(f"\n{dest.df}\n")
        else:
          weatherFile.write(f"\n- Min temp: {dest.min_temp} degrees\
                              \n- Max temp: {dest.max_temp} degrees\
                              \n- Wind speed: {dest.min_wind_speed} - {dest.max_wind_speed} mph\
                              \n- Wind gusts: {dest.min_wind_gusts} - {dest.max_wind_gusts} mph\n")
          if dest._moderate_rain == True:
            weatherFile.write(color.RED + f"\n[!] Moderate rain expected [!]\
                              \n\n\t[RAIN STATUS]\
                              \n----------------------------\
                              \n{dest.rain_status}\
                              \n----------------------------\n\n" + color.END)
          else:
            weatherFile.write(color.GREEN + f"\n[+] Moderate rain not expected [+]\n" + color.END)
          if (dest._light_rain == True and dest._moderate_rain == False):
            weatherFile.write(color.RED + f"\n[!] Light rain expected [!]\
                              \n\n\t[RAIN STATUS]\
                              \n----------------------------\
                              \n{dest.rain_status}\
                              \n----------------------------\n\n" + color.END)
          elif (dest._light_rain == False and dest._moderate_rain == False):
            weatherFile.write(color.GREEN + f"\n[+] Light rain not expected either [+]\
                              \n\t[+] HOOOORAH [+]" + color.END)
          weatherFile.write(f"\n{dest.df}\n\n" + color.BOLD + "---------------------------------------------------------------\
                              \n---------------------------------------------------------------\n\n\n\n" + color.END)

    weatherFile.close()

  @classmethod
  def display(cls):
    for dest in Destination.instances:
      if dest.active == True:
        dest._display_weather()

  def __init__(self, apikey, name, latitude, longitude, driving_minutes=None, camping=False, bouldering=False, swimming=False):
    self.apikey = apikey
    self.name = str(name)
    self.latitude = latitude
    self.longitude = longitude
    self.driving_minutes = int(driving_minutes)
    self.camping = camping
    self.bouldering = bouldering
    self.swimming = swimming
    self.forecast_type = None
    self.df = None
    self.one_call = None
    self.active = False
    self._moderate_rain = False
    self._light_rain = False
    
    Destination.instances.append(self)

  def __repr__(self):
    return self.name

  def weather(self, forecast_type='forecast_hourly', bldrng=False, cmpng=False, swmmng=False, drvng=800, args=0):
    fc = forecast_type
    if args == 1:
      if bldrng == True:
        if (self.bouldering == True and self.driving_minutes <= int(drvng)):
          self._gen_weather(forecast_type=fc)
      elif cmpng == True:
        if (self.camping == True and self.driving_minutes <= int(drvng)):
          self._gen_weather(forecast_type=fc)
      elif swmmng == True:
        if (self.swimming == True and self.driving_minutes <= int(drvng)):
          self._gen_weather(forecast_type=fc)
    elif args == 2:
      if (bldrng == True and cmpng == True):
        if (self.bouldering == True and self.camping == True and self.driving_minutes <= int(drvng)):
          self._gen_weather(forecast_type=fc)
      elif (bldrng == True and swmmng == True):
        if (self.bouldering == True and self.swimming == True and self.driving_minutes <= int(drvng)):
          self._gen_weather(forecast_type=fc)
      elif (swmmng == True and cmpng == True):
        if (self.swimming == True and self.camping == True and self.driving_minutes <= int(drvng)):
          self._gen_weather(forecast_type=fc)
    elif args == 3:
      if (self.bouldering == True and self.camping == True and self.swimming == True and self.driving_minutes <= int(drvng)):
        self._gen_weather(forecast_type=fc)

  def _gen_weather(self, forecast_type='forecast_hourly'):
    self.active = True
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

  # display output in relevant format
  def _display_weather(self):
    if (self.forecast_type == 'forecast_hourly' or self.forecast_type == 'forecast_daily'):
      self._display_forecast()
    elif self.forecast_type == 'current':
      self._display_current_weather()

  # build DataFrame formatted for hourly forecast
  def _forecast_hourly(self):
    self.df = pd.DataFrame({
                  'Date' : pd.Timestamp(i.reference_time(timeformat='date')).astimezone('America/Denver').date().strftime('%m-%d-%Y'),
                  'Time' : pd.Timestamp(i.reference_time(timeformat='date')).astimezone('America/Denver').time().strftime('%H:%M'),
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
                  'Date' : pd.Timestamp(i.reference_time(timeformat='date')).astimezone('America/Denver').date().strftime('%m-%d-%Y'),
                  # 'Time' : pd.Timestamp(i.reference_time(timeformat='date')).astimezone('America/Denver').time().strftime('%H:%M'),
                  'Rain %' : round(i.to_dict()['precipitation_probability']*100),
                  'Max Temp' : round(i.temperature(unit='fahrenheit')['max']),
                  'Min Temp' : round(i.temperature(unit='fahrenheit')['min']),
                  'Status' : i.to_dict()['status'],
                  'Wind Speed' : round(i.wind(unit='miles_hour')['speed']),
                  'Wind Gusts' : round(i.wind(unit='miles_hour')['gust'])
                  } for i in self.one_call).set_index(['Date'])
    self.min_temp = self.df['Min Temp'].min()
    self.max_temp = self.df['Max Temp'].max()
    self.min_wind_speed = self.df['Wind Speed'].min()
    self.max_wind_speed = self.df['Wind Speed'].max()
    self.min_wind_gusts = self.df['Wind Gusts'].min()
    self.max_wind_gusts = self.df['Wind Gusts'].max()

  # build DataFrame formatted for current weather
  def _current_weather(self):
    self.df = pd.DataFrame({
                  'Date' : pd.Timestamp(self.one_call.reference_time(timeformat='date')).astimezone('America/Denver').date().strftime('%m-%d-%Y'),
                  'Time' : pd.Timestamp(self.one_call.reference_time(timeformat='date')).astimezone('America/Denver').time().strftime('%H:%M'),
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

    if self.forecast_type == 'forecast_hourly':
      if self._light_rain == True:
        self._gen_light_rain_hourly()
      if self._moderate_rain == True:
        self._gen_moderate_rain_hourly()
    elif self.forecast_type == 'forecast_daily':
      if self._light_rain == True:
        self._gen_light_rain_daily()
      if self._moderate_rain == True:
        self._gen_moderate_rain_daily()

  # build DataFrame of dates/times when rain probability is >= 25%
  def _gen_moderate_rain_hourly(self):
    self.rain_over_25 = pd.DataFrame({'Date' : i[0], 'Time' : i[1], 'Rain %' : self.df['Rain %'][i]} \
                            for i in self.df['Rain %'].index \
                            if self.df['Rain %'][i] >= 25)
    self._gen_rain_status_hourly()

  # build DataFrame of dates/times when rain probability is >= 10% and < 25%
  def _gen_light_rain_hourly(self):
    self.rain_over_10 = pd.DataFrame({'Date' : i[0], 'Time' : i[1], 'Rain %' : self.df['Rain %'][i]} \
                            for i in self.df['Rain %'].index \
                            if (self.df['Rain %'][i] >= 10 and self.df['Rain %'][i] < 25))
    self._gen_rain_status_hourly()

  # build DataFrame of dates/times when expected conditions are 'rainy'
  def _gen_rain_status_hourly(self):
    self.rain_status = pd.DataFrame({'Date' : i[0], 'Time' : i[1], 'Weather' : self.df['Status'][i]} \
                            for i in self.df['Status'].index \
                            if self.df['Status'][i] == 'Rain')

   # build DataFrame of dates/times when rain probability is >= 25%
  def _gen_moderate_rain_daily(self):
    self.rain_over_25 = pd.DataFrame({'Date' : i, 'Rain %' : self.df['Rain %'][i]} \
                            for i in self.df['Rain %'].index \
                            if self.df['Rain %'][i] >= 25)
    self._gen_rain_status_daily()

  # build DataFrame of dates/times when rain probability is >= 10% and < 25%
  def _gen_light_rain_daily(self):
    self.rain_over_10 = pd.DataFrame({'Date' : i, 'Rain %' : self.df['Rain %'][i]} \
                            for i in self.df['Rain %'].index \
                            if (self.df['Rain %'][i] >= 10 and self.df['Rain %'][i] < 25))
    self._gen_rain_status_daily()

  # build DataFrame of dates/times when expected conditions are 'rainy'
  def _gen_rain_status_daily(self):
    self.rain_status = pd.DataFrame({'Date' : i, 'Weather' : self.df['Status'][i]} \
                            for i in self.df['Status'].index \
                            if self.df['Status'][i] == 'Rain')

  # display output formatted to forecast_type='forecast_hourly' or 'forecast_daily'  
  def _display_forecast(self):
    print("\n\t" + color.CYAN + "*"*len(self.name) + "**" + color.END)
    print(color.CYAN + "\t*" + color.END + color.BOLD + f"{self.name.upper()}" + color.END + color.CYAN + "*" + color.END)
    print("\t" + color.CYAN + "*"*len(self.name) + "**" + color.END)
    print(f"\n- Driving minutes: {self.driving_minutes}\n")
    print(f"\n- Bouldering: {self.bouldering}")
    print(f"- Camping: {self.camping}")
    print(f"- Swimming: {self.swimming}\n")
    if self._moderate_rain == True:
      print(color.RED + f"[!] MODERATE RAIN EXPECTED [!]" + color.END)
      print(f"{self.rain_over_25}\n")
      print(f"{self.rain_status}")
      print(color.RED + f"[!] MODERATE RAIN EXPECTED [!]\n\n" + color.END)
    else:
      print(color.GREEN + f"[+] MODERATE RAIN NOT EXPECTED [+]\n" + color.END)
    if (self._light_rain == True and self._moderate_rain == False):
      print(color.RED + f"[!] LIGHT RAIN EXPECTED [!]" + color.END)
      print(f"{self.rain_over_10}\n")
      print(f"{self.rain_status}")
      print(color.RED + f"[!] LIGHT RAIN EXPECTED [!]\n\n" + color.END)
    elif (self._light_rain == False and self._moderate_rain == False):
      print(color.GREEN + f"[+] LIGHT RAIN NOT EXPECTED [+]\n" + color.END)

    print("** Max temp: " + color.BOLD + f"{self.max_temp} degrees" + color.END)
    print("** Min temp: " + color.BOLD + f"{self.min_temp} degrees" + color.END)
    print("** Wind speed: " + color.BOLD + f"{self.min_wind_speed} - {self.max_wind_speed} mph" + color.END)
    print("** Wind gusts: " + color.BOLD + f"{self.min_wind_gusts} - {self.max_wind_gusts} mph" + color.END)
    print(f"\n\n{self.df}\n")
    print(color.BLUE + "-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------\n\n" + color.END)

  # display output formatted to forecast_type='current'
  def _display_current_weather(self):
    print("\n\t\t" + color.CYAN + "*"*len(self.name) + "**" + color.END)
    print(color.CYAN + "\t\t*" + color.END + color.BOLD + f"{self.name.upper()}" + color.END + color.CYAN + "*" + color.END)
    print("\t\t" + color.CYAN + "*"*len(self.name) + "**" + color.END)
    print(f"\nDriving minutes: {self.driving_minutes}\n")
    print(f"\nBouldering: {self.bouldering}")
    print(f"Camping: {self.camping}")
    print(f"Swimming: {self.swimming}\n")
    print("\n", self.df, "\n")
    print(color.BLUE + "-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------\n\n" + color.END)

# generate Destinations
def gen_destinations(apikey):
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

def welcome_banner():
  print()
  print(color.BLUE_BG + "                                                                                            " + color.BOLD + "github.com/blagodellago " + color.END)
  print(color.BLUE_BG + "                                     " + color.BOLD + "...Where can I climb?..." + "                                                       " + color.END)
  print(color.BLUE_BG + "                                     " + color.BOLD + "...Where can I camp?..." + "                                                        " + color.END)
  print(color.BLUE_BG + "                                     " + color.BOLD + "...Where can I swim?..." + "                                                        " + color.END)
  print(color.BLUE_BG + "                                                                                                                    " + color.END)
  print(color.BLUE_BG + "                                                                                                                    " + color.END)
  print(color.BLUE_BG + "         "  + color.END + color.LIGHTGREY + "/\\" + color.END + color.BLUE_BG + "             ___                                                                                         " + color.END)
  print(color.BLUE_BG + "        " + color.END + color.LIGHTGREY + "/##\\" + color.BLUE_BG + "      " + color.END + color.LIGHTGREY + "/\\" + color.END + color.BLUE_BG + "   " + color.END + color.LIGHTGREY + "/###\\" + color.END + color.BLUE_BG + "                                                                                        " + color.END)
  print(color.BLUE_BG + "       " + color.END + color.LIGHTGREY + "/####" + color.LIGHTGREEN + "^" + color.LIGHTGREY + "#\\" + color.END + color.BLUE_BG + "  " + color.END + color.LIGHTGREY + "/##\\/###" + color.LIGHTGREEN + "^^^" + color.LIGHTGREY + "\\" + color.END + color.BLUE_BG + "_                                                                                      " + color.END)
  print(color.BLUE_BG + "      " + color.END + color.LIGHTGREY + "/#" + color.LIGHTGREEN + "^" + color.LIGHTGREY + "##" + color.LIGHTGREEN + "^^" + color.LIGHTGREY + "##\\/###" + color.LIGHTGREEN + "^^" + color.LIGHTGREY + "###" + color.LIGHTGREEN + "^^^" + color.LIGHTGREY + "###\\" + color.END + color.BLUE_BG + "                                                                                    " + color.END)
  print(color.BLUE_BG + "     " + color.END + color.LIGHTGREY + "/" + color.GREEN + "^^^" + color.LIGHTGREY + "#" + color.LIGHTGREEN + "^^^^^" + color.LIGHTGREY + "#\\##" + color.LIGHTGREEN + "^^^^^" + color.LIGHTGREY + "##" + color.LIGHTGREEN + "^^^^" + color.LIGHTGREY + "##\\" + color.END + color.BLUE_BG + "                                                                                   " + color.END)
  print(color.BLUE_BG + "    " + color.END + color.LIGHTGREY + "/" + color.LIGHTGREEN + "^^^^^^^^^^^^^^^^^^^^^^^^^^^" + color.LIGHTGREY + "#\\" + color.END + color.BLUE_BG + "                                                                                  " + color.END)
  print(color.BLUE_BG + "   " + color.END + color.LIGHTGREY + "/" + color.LIGHTGREEN + "@@@@" + color.END + color.BOLD + "WEATHER FOR MY FAVORITE" + color.END + color.LIGHTGREEN + "@@@" + color.END + color.LIGHTGREY + "\\" + color.END + color.BLUE_BG + "                                                                                 " + color.END)
  print(color.BLUE_BG + "  " + color.END + color.LIGHTGREY + "/" + color.LIGHTGREEN + "@@@@@" + color.END + color.BOLD + "RECREATION DESTINATIONS" + color.END + color.LIGHTGREEN + "@@@@" + color.END + color.LIGHTGREY + "\\" + color.END + color.BLUE_BG + "                                                                                " + color.END)
  print(color.BLUE_BG + " " + color.END + color.LIGHTGREY + "/" + color.LIGHTGREEN + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" + color.END + color.LIGHTGREY + "\\" + color.END + color.BLUE_BG + "                                                                               " + color.END)
  print("\n\n\n\n\n")

# accept command line options
argumentList = sys.argv[1:]
options = "a:wdbcsm:f:"
long_options = ["apikey", "write", "display", "bouldering", "camping", "swimming", "minutes", "forecast"]

try:
  os.system('cls' if os.name == 'nt' else 'clear')
  welcome_banner()
  arguments, values = getopt.getopt(argumentList, options, long_options)
  bouldering = False
  camping = False
  swimming = False
  write = False
  display = False
  forecast = 'forecast_hourly'
  driving_limit = 0
  args = 0
  load_activities = []
  for currentArgument, currentValue in arguments:
    if currentArgument in ("-a", "--apikey"):
      apikey = currentValue
    if currentArgument in ("-w", "--write"):
      write = True
    elif currentArgument in ("-d", "--display"):
      display = True
    elif currentArgument in ("-b", "--bouldering"):
      bouldering = True
      if bouldering == True:
        load_activities.append('bouldering')
      args += 1
    elif currentArgument in ("-c", "--camping"):
      camping = True
      if camping == True:
        load_activities.append('camping')
      args += 1
    elif currentArgument in ("-s", "--swimming"):
      swimming = True
      if swimming == True:
        load_activities.append('swimming')
      args += 1
    elif currentArgument in ("-m", "--minutes"):
      driving_limit = int(currentValue)
    elif currentArgument in ("-f", "--forecast"):
      forecast = currentValue

  if apikey == None:
    print("Please supply an apikey [-a <apikey>] to request weather from PYOWM")
  else:
    gen_destinations(apikey)

  for dest in Destination.instances:
    dest.weather(forecast_type=forecast, bldrng=bouldering, cmpng=camping, swmmng=swimming, drvng=driving_limit, args=args)

  if write == True:
    Destination.output(forecast)

  if display == True:
    Destination.display()

except getopt.error as err:
  # output error, and return with an error code
  print(str(err))