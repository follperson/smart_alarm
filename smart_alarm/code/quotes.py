#!/usr/bin/env python3
from requests import get
from bs4 import BeautifulSoup
from .config import api_key_weather


def get_forecast_entry(table):
    """ collect all the information about the weather for today/tonight """
    entries = table.find_all('div')
    for i in entries:
        if i.text == 'Today':
            return i
    for i in entries:
        if i.text == 'Tonight':
            return i


def get_weather_nws(location='MapClick.php?textField1=38.96&textField2=-77.03'): # todo make it more flexible with location?
    """
      get weather data from the National Weather Services, parsing using Beatuiful Soup
    """
    # get the weather for the location
    page = get('https://forecast.weather.gov/' + location)
    soup = BeautifulSoup(page.content, features='html.parser')
    detail_forecast_table = soup.find('div', {'id': 'detailed-forecast-body'})
    today = get_forecast_entry(detail_forecast_table)
    if today is None:
        print('Cannot find today info on NWS website')
        raise FileNotFoundError
    long_text = today.find_next('div').text
    long_text = 'Good Morning! ... ' + long_text
    return long_text


def check_in_dict(d, check):
    if check in d:
        return d[check]
    else:
        return None


def calculate_real_feel(temp, humidity, wind_speed):
    # https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
    heat_index = -42.379 + 2.04901523 * temp + 10.14333127 * humidity - .22475541 * temp * humidity - \
                 .00683783 * temp **2 - .05481717 * humidity**2 + .00122874 * temp**2 * humidity + \
                 .00085282 * temp * humidity **2 - .00000199 * temp **2 * humidity ** 2

    # https://www.weather.gov/media/epz/wxcalc/windChill.pdf
    wind_chill = 35.74 + (0.6215 * temp) - (35.75 * wind_speed ** 0.16) + (0.4275 * temp * wind_speed ** 0.16)

    return heat_index, wind_chill

def convert_kelvin(temp_k):
    return (temp_k - 273.15) * 9 / 5 + 32


def parse_owm(info):
    clouds = info['clouds']['all']
    humidity = info['main']['humidity']
    temp = convert_kelvin(info['main']['temp'])
    pressure = info['main']['pressure']
    weather_desc = [i['main'] for i in info['weather']]
    wind_speed = info['wind']['speed']
    wind_dir = info['wind']['deg']
    rain = check_in_dict(info, 'rain')
    snow = check_in_dict(info, 'snow')
    if rain:
        rain = rain['1h']
    if snow:
        snow = snow['1h']
    heat_index, wind_chill = calculate_real_feel(temp, humidity, wind_speed)
    resp = []
    if not rain:
        if snow:
            resp.append('Look outside, it\'s snowing!')
    else:
        if rain > .3:
            resp.append('Watch out, it\'s pouring outside.')
        elif rain > .1:
            resp.append('It\' raining a bit outside.')
        else:
            resp.append("It\'s drizzling outside.")
    if temp < 75: # only report wind_chill if its cold, 
        if wind_chill > temp:
            report_temp = temp
        else:
            report_temp = wind_chill
    else:  # only report heat_index if it is hot
        report_temp = heat_index

    resp.append('The current weather is %s.' % ', or '.join(weather_desc))
    resp.append('The temperature is %s degrees.' % str(int(report_temp)))
    resp.append('Cloud cover is at %s percent.' % str(clouds))
    return '\n'.join(resp)

def get_weather_owm(zipcode='20011'):
    resp = get('https://api.openweathermap.org/data/2.5/weather?zip=%s,us&APPID=%s' % (zipcode, api_key_weather))
    info = resp.json()
    text = parse_owm(info)
    return text


def get_quote():
    resp = get('http://quotes.rest/qod.json')
    if resp.status_code == 429:
        return 'Hey ho cowboy, you are going too fast. Please refrain from going so fast', 'Andrew Follmann'
    quote_dict = resp.json()
    quote_body = quote_dict['contents']['quotes'][0]
    text = quote_body['quote']
    author = quote_body['author']
    return text + '. Quote by: ' + author

