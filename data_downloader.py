import argparse
import sys
import urllib.request
import zipfile
from itertools import product
from pathlib import Path

import geopandas as gpd
import numpy as np
import requests
from tqdm import tqdm

SPAM_TIF_URLS = [
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_harv_area.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_phys_area.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_yield.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_prod.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_val_prod_agg.geotiff.zip",
    ]
AREAS_URL = "https://raw.githubusercontent.com/Vizzuality/science-code-challenge/main/areas.geojson"
CROP_TYPE = "SOYB"
FOREST_CHANGE_SOURCES_URL = "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2020-v1.8/lossyear.txt"


def download_and_unzip_soybeam(urls: list[str], data_dir: Path):
    zip_files = []
    # download everything
    for url in (pbar := tqdm(urls)):
        pbar.set_description(f"Downloading SPAM data")

        filename = url.split("/")[-1]
        zip_file = data_dir / filename

        pbar.set_postfix_str(filename)
        urllib.request.urlretrieve(url, filename=zip_file)
        zip_files.append(zip_file)

    # unzip only the needed images given CROP_TYPE
    for zip_file in (pbar := tqdm(zip_files)):
        pbar.set_description(f"Unzipping soy beam images")
        dest_dir = data_dir / zip_file.name.removesuffix(".geotiff.zip")
        with zipfile.ZipFile(zip_file, 'r') as src:
            # filter images in the zip that contain the required crop type label
            soybeam_images = [fname for fname in src.namelist() if CROP_TYPE in fname]
            src.extractall(dest_dir, members=soybeam_images)

        zip_file.unlink(missing_ok=True)


def expand_bbox_to_nearest_tens(bbox: gpd.GeoSeries) -> gpd.GeoSeries:
    bbox = bbox.copy()
    bbox.minx = np.floor(bbox.minx // 10) * 10
    bbox.maxx = np.ceil(bbox.maxx // 10) * 10
    bbox.miny = np.floor(bbox.miny // 10) * 10
    bbox.maxy = np.ceil(bbox.maxy // 10) * 10
    return bbox.astype(int)


def format_lat(lat: int) -> str:
    return f"{lat:02d}N" if lat >= 0 else f"{abs(lat):02d}S"


def format_lon(lon: int) -> str:
    return f"{lon:03d}E" if lon >= 0 else f"{abs(lon):03d}W"


def make_granules_from_extend(bbox: gpd.GeoSeries, base_name):
    """Makes granules for downloading loss forest data."""
    longitudes = range(bbox.miny, bbox.maxy + 10, 10)
    latitudes = range(bbox.minx, bbox.maxx + 10, 10)
    return [f"{base_name}_{format_lat(lat)}_{format_lon(lon)}.tif" for lat, lon in product(longitudes, latitudes)]


if __name__ == "__main__":
    print("""██╗   ██╗██╗███████╗███████╗██╗   ██╗ █████╗ ██╗     ██╗████████╗██╗   ██╗
██║   ██║██║╚══███╔╝╚══███╔╝██║   ██║██╔══██╗██║     ██║╚══██╔══╝╚██╗ ██╔╝
██║   ██║██║  ███╔╝   ███╔╝ ██║   ██║███████║██║     ██║   ██║    ╚████╔╝ 
╚██╗ ██╔╝██║ ███╔╝   ███╔╝  ██║   ██║██╔══██║██║     ██║   ██║     ╚██╔╝  
 ╚████╔╝ ██║███████╗███████╗╚██████╔╝██║  ██║███████╗██║   ██║      ██║   
  ╚═══╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝      ╚═╝   
  
  Data downloader for the code challenge.
  
  """)
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("data_dir", type=str, help="Directory where to download the data", default="data")
    parser.add_argument("-f", action="store_true", help="Force downloading without asking permission")
    args = parser.parse_args()

    base_data_dir = Path("./") / args.data_dir
    base_data_dir.mkdir(exist_ok=True)

    if args.f:  # don't ask for user input
        print(f"Downloading data into {base_data_dir.absolute()}")
    else:  # ask for user input to continue the download
        if not input(f"I'm about to download the data into {base_data_dir.absolute()}.\n"
                     "Do you want to continue (yes/no)?: ").lower() in ["yes", "y"]:
            print("Canceling...")
            sys.exit(0)

    # download_and_unzip_soybeam(SPAM_TIF_URLS, base_data_dir)

    print(f"Downloading areas.geojson...")
    areas_filename = base_data_dir / AREAS_URL.split("/")[-1]
    urllib.request.urlretrieve(AREAS_URL, filename=areas_filename)

    # Retrieve Global Forest Change data for the regions in areas.geojson
    areas = gpd.read_file(areas_filename)
    # buffer the bounding boxes of the areas, so we can download all the 10x10 degree tiles that contain data
    # in the regions of areas.geojson
    rounded_areas_bounds = areas.geometry.bounds.apply(expand_bbox_to_nearest_tens, axis=1)

    req = requests.get(FOREST_CHANGE_SOURCES_URL)
    forest_change_urls = req.text.split("\n")
    donor_filenames = forest_change_urls[0].split("/")[-1]
    *filename_base, _, _ = donor_filenames.removesuffix(".tif").split("_")
    target_filenames = []
    for _, bbox in rounded_areas_bounds.iterrows():
        target_filenames.extend(make_granules_from_extend(bbox, "_".join(filename_base)))

    forest_change_urls_in_areas = [url for url in forest_change_urls if Path(url).name in target_filenames]

    base_forest_data_dir = base_data_dir / "forest"
    base_forest_data_dir.mkdir(exist_ok=True)
    # download the forest change images
    for url in (pbar := tqdm(forest_change_urls_in_areas)):
        filename = Path(url).name
        pbar.set_description(f"Downloading forest change data")
        pbar.set_postfix_str(filename)
        urllib.request.urlretrieve(url, filename=base_forest_data_dir / filename)
    print("\nAll done! (ง ͡ʘ ͜ʖ ͡ʘ)ง")
