import aiml
import os
import requests
import json
import time

kernel = aiml.Kernel()

# load every aiml file in the 'standard' directory
dirname = 'aiml_data'
filenames = [os.path.join(dirname, f) for f in os.listdir(dirname)]
aiml_filenames = [f for f in filenames if os.path.splitext(f)[1]=='.aiml']

kernel = aiml.Kernel()
for filename in aiml_filenames:
  kernel.learn(filename)

google_key =
darksky_key = 

CACHE_FNAME = 'cache.json'

#### GENERAL CACHE FUNC ####
try:
  cache_file = open(CACHE_FNAME, 'r')
  cache_contents = cache_file.read()
  cache_file.close()
  CACHE_DICTION = json.loads(cache_contents)
except:
  CACHE_DICTION = {}

def getWithCaching(baseURL, params={}):

    req = requests.Request(method = 'GET', url = baseURL, params = sorted(params.items()))
    prepped = req.prepare()
    fullURL = prepped.url

    # if we haven't seen this URL before
    if fullURL not in CACHE_DICTION:
    # make the request and store the response
        response = requests.Session().send(prepped)
        CACHE_DICTION[fullURL] = response.text

    # write the updated cache file
        cache_file = open(CACHE_FNAME, 'w')
        cache_file.write(json.dumps(CACHE_DICTION))
        cache_file.close()

    elif fullURL in CACHE_DICTION and 'darksky' in fullURL:
        if time.time() > (json.loads(CACHE_DICTION[fullURL])['currently']['time'] + (60*5)):
            print ("New Data...")
            response = requests.Session().send(prepped)
            CACHE_DICTION[fullURL] = response.text
            cache_file = open(CACHE_FNAME, 'w')
            cache_file.write(json.dumps(CACHE_DICTION))
            cache_file.close()
            return CACHE_DICTION[fullURL]

    return CACHE_DICTION[fullURL]


def RegResponse(city, state):
    return '{}, eh? Do you like it in {}?'.format(state, city)
kernel.addPattern("I live in {city}, {state}", RegResponse)

def LatLongRequest(city_name):
  req = getWithCaching("https://maps.googleapis.com/maps/api/geocode/json?", params = {
  "address":city_name,
  "key": google_key
  })
  result = json.loads(req)
  return(result["results"][0]["geometry"]["location"])

def WeatherRequest(city):
  try:
    LatLongDict = LatLongRequest(city)
    lat = LatLongDict["lat"]
    longitude = LatLongDict["lng"]
    request = getWithCaching("https://api.darksky.net/forecast/{}/{},{}".format(darksky_key,lat,longitude))
    data = json.loads(request)
    return data
  except:
    return "Sorry, I don't know."

# 2 rain kernel functions - one for the week, one for today
def RainToday(city):
  try:
    weather = WeatherRequest(city)
    prob = weather["currently"]['precipProbability']
    if prob < 0.1:
      return "It almost definitely will not rain in " + city
    elif prob >= 0.1 and prob < 0.5:
      return "It probably will not rain in " + city
    elif prob >= 0.5 and prob < 0.9:
      return "It probably will rain in " + city
    elif prob >= 0.9:
      return "It will almost definitely rain in " + city
    else:
      return errorFunc(city)
  except:
    return errorFunc(city)
kernel.addPattern("Is it going to rain in {city} today?", RainToday)

#1-((probability it will NOT rain on day 1) * (probability it will NOT rain on day 2) * ... * (probability it will NOT rain on day 7))
def RainWeek(city):
  try:
    weather = WeatherRequest(city)
    dayOne = 1 - weather['daily']['data'][0]['precipProbability']
    dayTwo = 1 - weather['daily']['data'][1]['precipProbability']
    dayThree = 1 - weather['daily']['data'][2]['precipProbability']
    dayFour = 1 - weather['daily']['data'][3]['precipProbability']
    dayFive = 1 - weather['daily']['data'][4]['precipProbability']
    daySix = 1 - weather['daily']['data'][5]['precipProbability']
    daySeven = 1 - weather['daily']['data'][6]['precipProbability']
    multiplied = (dayOne * dayTwo * dayThree * dayFour * dayFive * daySix * daySeven)
    WeekProb = 1 - multiplied
    if WeekProb < 0.1:
      return "It almost definitely will not rain in " + city
    elif WeekProb >= 0.1 and WeekProb < 0.5:
      return "It probably will not rain in " + city
    elif WeekProb >= 0.5 and WeekProb < 0.9:
      return "It probably will rain in " + city
    elif WeekProb >= 0.9:
      return "It will almost definitely rain in " + city
    else:
      return errorFunc(city)
  except:
    return errorFunc(city)
kernel.addPattern("Is it going to rain in {city} this week?", RainWeek)

#general what is weather like function
def generalWeather(city):
  try:
    weather = WeatherRequest(city)
    general = weather["currently"]["summary"]
    temperature = weather["currently"]["temperature"]
    return "Right now in {}, it's {} degrees and {}!".format(city, temperature, general)
  except:
    return errorFunc(city)
kernel.addPattern("What's the weather like in {city}?", generalWeather)

#daily hot or cold functions
def HeatFunc(city):
  try:
    weather = WeatherRequest(city)
    MaxTemp = weather['daily']['data'][0]["temperatureMax"]
    return "In {} it will reach {} degrees".format(city, MaxTemp)
  except:
    return errorFunc(city)
kernel.addPattern("How hot will it get in {city} today?", HeatFunc)

def ColdFunc(city):
  try:
    weather = WeatherRequest(city)
    MinTemp = weather['daily']['data'][0]["temperatureMin"]
    return "In {} the coldest it will be is {} degrees".format(city, MinTemp)
  except:
    return errorFunc(city)
kernel.addPattern("How cold will it get in {city} today?", ColdFunc)

# week heat or cold functions
def WeekHeatFunc(city):
  try:
    weather = WeatherRequest(city)
    MaxTemp = float(weather['daily']['data'][0]['temperatureMax'])
    for x in weather["daily"]["data"]:
      if float(x["temperatureMax"]) > MaxTemp:
        MaxTemp = float(x['temperatureMax'])
    return "In {} the high this week will be {} degrees".format(city, MaxTemp)
  except:
    return errorFunc(city)
kernel.addPattern("How hot will it get in {city} this week?", WeekHeatFunc)

def WeekColdFunc(city):
  try:
    weather = WeatherRequest(city)
    MinTemp = float(weather["daily"]["data"][0]["temperatureMin"])
    for x in weather["daily"]["data"]:
      if float(x["temperatureMin"]) < MinTemp:
        MinTemp = float(x["temperatureMin"])
    return "In {} the coldest this week will be {} degrees".format(city, MinTemp)
  except:
    return errorFunc(city)
kernel.addPattern("How cold will it get in {city} this week?", WeekColdFunc)

def errorFunc(city):
  return("is " + city + "a city?")

while(True):
  user_input = input("Ask whatever you want!: ")
  if user_input == "exit":
    print ("See ya later!")
    break
  else:
    print(kernel.respond(user_input))

        #
		# if len(songs) != 0:
		# 	print("-- SONGS --")
		# 	for x in songs:
		# 		print(str(accum_num) + "." + x[0])
		# 		accum_num += 1
		# else:
		# 	print("-- SONGS --")
		# 	print("There appear to be no songs.")
        #
		# if len(movies) != 0:
		# 	print("-- MOVIES --")
		# 	for x in movies:
		# 		print(str(accum_num) + "." + x[0])
		# 		accum_num += 1
		# else:
		# 	print("-- MOVIES --")
		# 	print("There appear to be no movies.")
        #
		# if len(other) != 0:
		# 	print("-- OTHER MEDIA --")
		# 	for x in other:
		# 		print(str(accum_num) + "." + x[0])
		# 		accum_num += 1
		# else:
		# 	print("-- OTHER MEDIA --")
		# 	print("There appears to be no other media.")
