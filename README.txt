Return weather forecasts for local and further afield recreation destinations.

[Apikey: (-a, --apikey <apikey>)]
[Recreational activities: bouldering (-b, --bouldering), camping (-c, --camping), swimming (-s, --swimming)]
[Driving distance in minutes: (-m, --minutes <minutes>=int)]
[Output options: display in terminal (-d, --display), write to file to camping-weather/WeatherOutput/ (-w, --write)]
[Forecast options: 'current', forecast_hourly', 'forecast_daily' (-f, --forecast <forecast_type>)]

Examples:

- Write daily weather forecasts for destinations with bouldering and camping within a 2 hour drive:

> python3 main.py -a <apikey> -bcwm 120 -f 'forecast_hourly'


- Display current weather forecasts for all swimming destinations:
> python3 main.py -a <apikey> -sd -f 'current'