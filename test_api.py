#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
from datetime import datetime, timezone

import pytest
import requests

import api


def get_remote_zones() -> list:
    r = requests.get('https://api.weather.gov/products/types/CWF/locations')
    r.raise_for_status()
    return r.json()["locations"].keys()


def download_test_data(zone: str):
    data = api.get_remote_forecast(zone)
    if 'error' in data:
        raise ValueError(
            f'Error getting forecast for zone {zone}',
            data["error"],
        )

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    with open(f'test/{zone}-{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_test_data() -> list:
    for root, dirs, files in os.walk("./test"):
        for name in files:
            yield os.path.join(root, name)


# https://api.weather.gov/products/types/CWF/locations
@pytest.mark.integration
@pytest.mark.parametrize("zone", get_remote_zones())
def test_parse_remote_forecasts(zone):
    region_forecast = api.parse_remote_forecast(zone)
    _test_region_forecast(region_forecast)


@pytest.mark.parametrize("file", get_test_data())
def test_parse_cached_forecasts(file):
    with open(file) as forecast_file:
        cached_forecast = json.load(forecast_file)

    region_forecast = api.parse_forecast(cached_forecast)
    _test_region_forecast(region_forecast)

def _test_region_forecast(region_forecast):
    assert region_forecast
    assert region_forecast["preamble"]

    if "synopsis" in region_forecast["preamble"].lower():
        assert region_forecast["short_synopsis"]

    for forecast in region_forecast["forecasts"]:
        assert forecast["forecast_date"]

# run ./test_api.py NNN to download test data for zone NNN
if __name__ == '__main__':
    if len(sys.argv) == 2:
        download_test_data(sys.argv[1])
