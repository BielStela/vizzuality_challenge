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
        with zipfile.ZipFile(zip_file, "r") as src:
            # filter images in the zip that contain the required crop type label
            soybeam_images = [fname for fname in src.namelist() if CROP_TYPE in fname]
            src.extractall(dest_dir, members=soybeam_images)

        zip_file.unlink(missing_ok=True)


def buffer_bbox_to_upper_left_tens(bbox: tuple) -> gpd.GeoSeries:
    # todo: Clarify what is going on here
    buffered_bbox = gpd.GeoSeries()
    buffered_bbox["minx"] = np.floor(bbox[0] // 10) * 10
    buffered_bbox["maxx"] = np.floor(bbox[2] // 10) * 10

    buffered_bbox["miny"] = (bbox[1] // 10 + 1) * 10
    buffered_bbox["maxy"] = (bbox[3] // 10 + 1) * 10
    return buffered_bbox.astype(int)


def format_lat(lat: int) -> str:
    return f"{lat:02d}N" if lat >= 0 else f"{abs(lat):02d}S"


def format_lon(lon: int) -> str:
    return f"{lon:03d}E" if lon >= 0 else f"{abs(lon):03d}W"


def make_granules_from_bounds(bbox: gpd.GeoSeries, base_name):
    """Makes granules for downloading loss forest data."""
    longitudes = range(bbox.miny, bbox.maxy + 10, 10)
    latitudes = range(bbox.minx, bbox.maxx + 10, 10)
    return [
        f"{base_name}_{format_lat(lat)}_{format_lon(lon)}.tif"
        for lat, lon in product(longitudes, latitudes)
    ]


if __name__ == "__main__":
    print(
        """██╗   ██╗██╗███████╗███████╗██╗   ██╗ █████╗ ██╗     ██╗████████╗██╗   ██╗
██║   ██║██║╚══███╔╝╚══███╔╝██║   ██║██╔══██╗██║     ██║╚══██╔══╝╚██╗ ██╔╝
██║   ██║██║  ███╔╝   ███╔╝ ██║   ██║███████║██║     ██║   ██║    ╚████╔╝ 
╚██╗ ██╔╝██║ ███╔╝   ███╔╝  ██║   ██║██╔══██║██║     ██║   ██║     ╚██╔╝  
 ╚████╔╝ ██║███████╗███████╗╚██████╔╝██║  ██║███████╗██║   ██║      ██║   
  ╚═══╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝      ╚═╝   
  
  Data downloader for the code challenge.
  
"""
    )
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "data_dir",
        type=str,
        help="Directory where to download the data",
        default="data",
    )
    parser.add_argument(
        "-f", action="store_true", help="Force downloading without asking permission"
    )
    args = parser.parse_args()

    base_data_dir = Path("./") / args.data_dir
    base_data_dir.mkdir(exist_ok=True)

    if args.f:  # don't ask for user input
        print(f"Downloading data into {base_data_dir.absolute()}")
    else:  # ask for user input to continue the download
        if not input(
            f"I'm about to download the data into {base_data_dir.absolute()}.\n"
            "Do you want to continue (yes/no)?: "
        ).lower() in ["yes", "y"]:
            print("Canceling...")
            sys.exit(0)

    download_and_unzip_soybeam(SPAM_TIF_URLS, base_data_dir)

    print(f"Downloading areas.geojson...")
    areas_filename = base_data_dir / AREAS_URL.split("/")[-1]
    urllib.request.urlretrieve(AREAS_URL, filename=areas_filename)

    # areas.geojson will be used to retrieve the necessary tiles of forest data
    areas = gpd.read_file(areas_filename)
    areas["region"] = ["india", "america"]

    base_forest_data_dir = base_data_dir / "forest"
    base_forest_data_dir.mkdir(exist_ok=True)

    # get the available images urls list
    req = requests.get(FOREST_CHANGE_SOURCES_URL)
    forest_change_urls = req.text.split("\n")
    # use an arbitrary url to get the file name structure
    donor_filename = forest_change_urls[0].split("/")[-1]
    *filename_base, _, _ = donor_filename.removesuffix(".tif").split("_")

    # Retrieve Global Forest Change data
    for _, area in areas.iterrows():
        # buffer the bounding boxes of the areas, so we can download all the 10x10 degree tiles that contain data
        # in the area. Uses GeoSeries because the .bounds method returns a nice dataframe with the bound labels
        buffered_area_bounds = buffer_bbox_to_upper_left_tens(area.geometry.bounds)
        target_filenames = make_granules_from_bounds(
            buffered_area_bounds, "_".join(filename_base)
        )
        forest_change_urls_in_area = [
            url for url in forest_change_urls if Path(url).name in target_filenames
        ]

        forest_region_dir = base_forest_data_dir / area.region
        forest_region_dir.mkdir(exist_ok=True)
        # download the images
        for url in (pbar := tqdm(forest_change_urls_in_area)):
            filename = Path(url).name
            pbar.set_description(f"Downloading forest loss data for {area.region}")
            pbar.set_postfix_str(filename)
            urllib.request.urlretrieve(url, filename=forest_region_dir / filename)
    print("\nAll done! (ง ͡ʘ ͜ʖ ͡ʘ)ง")
