# Vizzuality Code Challenge

challenge docs: https://github.com/Vizzuality/science-code-challenge/blob/main/README.md

There are two ways to reproduce this project:

## Conda environment

If you have conda installed in your machine, clone the repo and run in the repo dir
```shell
conda env create --name vizzuality --file environment.yml
```
and activate the env with
```shell
conda activate vizzuality
```
then, in order to download the data needed for the project, use the downloader `data_downloader.py` like
```shell
python data_downloader.py data
```
this will create the dir `data/` in the project directory and download all the files into it.

## Docker

To create a container with the image definition provided in `Dockerfile` use
```shell
docker build -t vizzuality-challenge .
```
Note that it may take a while to build the image since it downloads everything.

Then run the container with
```shell
docker run -p 8888:8888 --rm vizzuality-challenge
```
Finally you can directly connect to the jupyter lab instance running in the docker by **copying the link displayed in the terminal**.
