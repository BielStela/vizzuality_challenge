import sys
import zipfile

from pathlib import Path

import urllib.request

tif_urls = [
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_harv_area.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_phys_area.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_yield.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_prod.geotiff.zip",
    "https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_val_prod_agg.geotiff.zip",
    ]

areas_url = "https://raw.githubusercontent.com/Vizzuality/science-code-challenge/main/areas.geojson"

CROP_TYPE = "SOYB"


def download_and_unzip(urls: list[str], data_dir: Path):
    data_dir.mkdir(exist_ok=True)
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


if __name__ == "__main__":
    data_dir = Path("./") / "data"
    if not input(f"I'm about to download the data into {data_dir.absolute()}.\n"
                 "Do you want to continue (yes/no)?: ").lower() in ["yes", "y"]:
        print("Canceling...")
        sys.exit(0)
    download_and_unzip(tif_urls, data_dir)

    print(f"Downloading areas.geojson...")
    urllib.request.urlretrieve(areas_url, filename=data_dir/areas_url.split("/")[-1])
    print("All done :)")

