import sys
import urllib.request
import zipfile
from itertools import product
from pathlib import Path

import geopandas as gpd
import requests

tif_urls = [
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_harv_area.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_phys_area.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_yield.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_prod.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_val_prod_agg.geotiff.zip",
    ]

areas_url = "https://raw.githubusercontent.com/Vizzuality/science-code-challenge/main/areas.geojson"

CROP_TYPE = "SOYB"

LOSS_YEAR_SOURCES_URL = "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2020-v1.8/lossyear.txt"


def download_and_unzip_soybeam(urls: list[str], data_dir: Path):
    for url in urls:
        filename = url.split("/")[-1]
        zip_file_path = data_dir / filename
        print(f"Downloading {filename}...")
        dest_dir = data_dir / filename.split(".")[0]

        if dest_dir.exists():
            if not input(f"Looks like {dest_dir} already exists.\n"
                         f"Do you want to continue and unzip data into it (yes/no)?").lower() in ["yes", "y"]:
                print("Skipping...")
                continue
        urllib.request.urlretrieve(url, filename=zip_file_path)
        print(f"unziping into {dest_dir}...")
        with zipfile.ZipFile(zip_file_path, 'r') as src:
            soybeam_files = [f for f in src.namelist() if CROP_TYPE in f]
            src.extractall(dest_dir, members=soybeam_files)

        zip_file_path.unlink(missing_ok=True)


def round_to_ten(val: float) -> int:
    """Round the value to the next ten """
    if val < 0:
        return (int(val // 10) - 1) * 10
    else:
        return (int(val // 10) + 1) * 10


def coord_as_int(coord: str) -> int:
    sign = -1 if coord[-1] in "SW" else 1
    return int(coord[:-1]) * sign


def format_lat(lat: int) -> str:
    return f"{lat}N" if lat > 0 else f"{lat}S"


def format_lon(lon: int) -> str:
    return f"{lon}E" if lon > 0 else f"{lon}W"


def make_granules_from_extend(bbox: gpd.GeoSeries, base_name, extension):
    """Makes granules for downloading loss forest data."""
    longitudes = list(range(bbox.miny, bbox.maxy, 10)) + [bbox.maxy]
    latitudes = list(range(bbox.minx, bbox.maxx, 10)) + [bbox.maxx]
    return [f"{base_name}_{format_lat(lat)}_{format_lon(lon)}" for lat, lon in product(longitudes, latitudes)]

if __name__ == "__main__":
    base_data_dir = Path("./") / "data"
    base_data_dir.mkdir(exist_ok=True)
    if not input(f"I'm about to download the data into {base_data_dir.absolute()}.\n"
                 "Do you want to continue (yes/no)?: ").lower() in ["yes", "y"]:
        print("Canceling...")
        sys.exit(0)
    download_and_unzip_soybeam(tif_urls, base_data_dir)

    print(f"Downloading areas.geojson...")
    areas_filename = base_data_dir / areas_url.split("/")[-1]
    urllib.request.urlretrieve(areas_url, filename=areas_filename)

    areas = gpd.read_file(areas_filename)
    bboxes = areas.geometry.bounds.round()

    req = requests.get(LOSS_YEAR_SOURCES_URL)
    req.text
