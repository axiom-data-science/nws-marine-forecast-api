#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import dateparser
import pytz
import requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

if os.environ.get('ENABLE_CORS', '0') == '1':
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r'.*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )


@app.get('/')
def get_root() -> dict:
    return {'status': 'ok'}


@app.get('/forecast/')
async def get_zones(request: Request) -> dict:
    r = requests.get('https://api.weather.gov/products/types/CWF/locations')
    r.raise_for_status()
    return r.json()["locations"]


@app.get('/forecast/{zone}/')
async def get_forecast(request: Request, zone: str) -> dict:
    return parse_remote_forecast(zone)


def get_synopsis(product_text: str) -> str:
    SYNOPSIS_PATTERN = r"synopsis([\s\S]*?)\$\$"

    # Get the first substring that matches the synopsis pattern
    synopsis_search = re.search(
        SYNOPSIS_PATTERN, product_text, re.IGNORECASE
    )

    match = ""
    if synopsis_search:
        synopsis = synopsis_search.group(1)

        # Sometimes the synopsis doesn't begin/end with `...` so we should assume it ends
        # with the first line break if we do not see bounding `...`
        if len(synopsis.split("...")) > 1:
            match = " ".join(re.split(r"\.\.\.", synopsis)[1:])
        elif len(synopsis.split("\n")) > 1:
            match = " ".join(re.split(r"\n", synopsis)[1:])

    match = match.replace("\n", " ").strip()

    return match


def get_remote_forecast(zone: str) -> dict:
    forecasts_url = (
        f'https://api.weather.gov/products/types/CWF/locations/{zone}'
    )
    r = requests.get(forecasts_url)
    r.raise_for_status()
    forecasts = r.json()['@graph']
    if not forecasts:
        return {'error': (
            f'No forecasts found, check {forecasts_url}'
            ' and/or https://api.weather.gov/products/types/CWF/locations'
        )}

    forecast_url = forecasts[0]['@id']
    r = requests.get(forecast_url)
    r.raise_for_status()
    remote_forecast = r.json()
    remote_forecast['source_url'] = forecast_url
    return r.json()


def parse_remote_forecast(zone: str) -> dict:
    remote_forecast = get_remote_forecast(zone)
    if 'error' in remote_forecast:
        return remote_forecast
    return parse_forecast(remote_forecast)


def parse_forecast(upstream_forecast: dict) -> dict:
    forecast_chunks = upstream_forecast['productText'].split('$$')

    # remove preamble section from start of forecast, removing blank lines
    preamble = [line.strip() for line in forecast_chunks.pop(0).splitlines()
                if line.strip() and line.strip() != '000']

    # Extract the synopsis from the product text
    synopsis = get_synopsis(upstream_forecast['productText'])

    forecasts = []
    unprocessed_chunks = []
    for forecast_chunk in forecast_chunks:
        forecast = {}
        lines = [line.strip() for line in forecast_chunk.splitlines()
                 if line.strip()]
        if not lines:
            continue

        # incldue the raw text forecast
        forecast["raw"] = "\n".join(lines)

        code = []
        while lines:
            line = lines.pop(0)
            code.append(line.rstrip('-').strip())
            if line.endswith('-'):
                break
        forecast['code'] = ' '.join(code)
        if not lines:
            unprocessed_chunks.append(forecast_chunk)
            continue

        location = []
        while lines:
            line = lines.pop(0)
            location.append(line.rstrip('-').strip())
            # if this line ends with - and the next line starts with
            # at least three numbers, assume that's the timestamp
            # and end location processing
            if line.endswith('-') and lines[0][:3].isnumeric():
                break
        forecast['location'] = ' '.join(location)
        if not lines:
            unprocessed_chunks.append(forecast_chunk)
            continue

        forecast_date_str = lines.pop(0).strip()
        forecast['forecast_date_original'] = forecast_date_str

        # times are sometimes duplicated in multiple time zones
        # we only need one
        forecast_date_str = forecast_date_str.split("/")[0].strip()

        time_sep_idx = forecast_date_str.index(' ') - 2
        forecast_date = dateparser.parse(
            forecast_date_str[:time_sep_idx] + ':' +
            forecast_date_str[time_sep_idx:])
        if forecast_date:
            forecast['forecast_date_local'] = forecast_date
            forecast['forecast_date'] = forecast_date.astimezone(pytz.utc)

        if lines[0].strip() == 'UPDATED':
            lines.pop(0)
            forecast['is_updated'] = True
        else:
            forecast['is_updated'] = False

        advisories = []
        subforecasts = {}
        unprocessed = []
        in_advisory = False
        advisory = []
        in_subforecast = None
        for line in lines:
            if line.startswith('...'):
                in_advisory = True

            if in_advisory:
                advisory.append(line.replace('...', '').strip())
                if line.endswith('...'):
                    in_advisory = False
                    advisories.append(' '.join(advisory))
                    advisory = []
                continue

            if line.startswith('.'):
                subforecast_start_line = line[1:].split('...')
                if len(subforecast_start_line) == 2:
                    in_subforecast = subforecast_start_line[0]
                    subforecasts[in_subforecast] = []
                    line = subforecast_start_line[1]

            if in_subforecast:
                subforecasts[in_subforecast].append(line.strip())
            else:
                unprocessed.append(line)

        forecast['advisories'] = advisories
        forecast['sub_forecasts'] = [{
                'timeframe': k,
                'forecast_text': ' '.join(v)
            } for k, v in subforecasts.items()]
        forecast['unprocessed'] = unprocessed
        forecasts.append(forecast)

    region_forecast = {
        'preamble': '\n'.join(preamble),
        'short_synopsis': synopsis,
        'forecasts': forecasts,
        'unprocessed': unprocessed_chunks
    }
    return region_forecast


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
