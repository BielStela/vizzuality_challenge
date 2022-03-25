import sys
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd

tif_urls = [
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_harv_area.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_phys_area.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_yield.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_prod.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_val_prod_agg.geotiff.zip",
    ]

areas_url = "https://raw.githubusercontent.com/Vizzuality/science-code-challenge/main/areas.geojson"

CROP_TYPE = "SOYB"


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


def make_granules_from_extend(bboxes: gpd.GeoDataFrame):
    """Makes granules for downloading loss forest data."""
    pass


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
