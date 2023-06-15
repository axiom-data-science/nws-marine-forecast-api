# nws-marine-forecast-api

Proxy requests to the National Weather Service's Coastal Waters Forecast
(served via https://api.weather.gov at https://api.weather.gov/products/types/CWF)
and parse results to json.

# Running

Initialize conda environment in standard fashion:

```
conda env update
```

Activate the environment

```
conda activate nws-marine-forecast-api
```

Run the service

```
./api.py
```

or

```
uvicorn api:app --host 0.0.0.0 --port 8000
```

Query the service

```
$ curl -sSL "http://localhost:8000/forecast/AJK/" | jq | head -n 20
{
  "source_url": "https://api.weather.gov/products/56f811c0-828d-4639-baa4-bbf99dcaa60c",
  "preamble": "FZAK51 PAJK 151210\nCWFAJK\nCoastal Waters Forecast for Southeast Alaska\nNational Weather Service JUNEAU AK\n410 AM AKDT Thu Jun 15 2023\nSoutheast Alaska Inside Waters from Dixon Entrance to Skagway\nWind forecasts reflect the predominant speed and direction\nexpected. Sea forecasts represent the average of the highest\none-third of the combined windwave and swell height.\nPKZ098-160245-\n410 AM AKDT Thu Jun 15 2023\n.SYNOPSIS FOR SOUTHEAST ALASKA INNER CHANNELS COASTAL WATERS...\nA gale force front arrives on Thursday. Areas of northerly winds\nin the panhandle will switch to southerly as the ridge breaks\ndown ahead of the front. East West channels will see enhanced\neasterly winds Thursday afternoon and through the night into\nFriday.",
  "forecasts": [
    {
      "code": "PKZ011-160245",
      "location": "Glacier Bay",
      "forecast_date_original": "410 AM AKDT Thu Jun 15 2023",
      "forecast_date_local": "2023-06-15T04:10:00-08:00",
      "forecast_date": "2023-06-15T12:10:00+00:00",
      "is_updated": false,
      "advisories": [],
      "sub_forecasts": [
        {
          "timeframe": "TODAY",
          "forecast_text": "N wind 10 kt becoming 15 kt in the afternoon. Seas 2 ft or less then 3 ft. Rain."
        },
        {
          "timeframe": "TONIGHT",
          "forecast_text": "N wind 15 kt becoming SE. Seas 3 ft. Rain."
```

# Run with Docker

Build the image

```
docker build -t nws-marine-forecast-api .
```

Run the image

```
docker run --rm -p 8000:8000 nws-marine-forecast-api
```

# Testing

Make sure to install dev dependencies into the conda environment

```
conda env update -f environment-dev.yml
```

Run tests against cached data

```
pytest
```

Also run integration tests against remote data for all zones

```
pytest --integration
```

Download cached data for a zone for non-integration testing

```
./test_api.py AJK
```
