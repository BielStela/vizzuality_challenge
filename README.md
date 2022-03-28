# Vizzuality Code Challenge


This repository contains my solution to the [Vizzuality code challenge](https://github.com/Vizzuality/science-code-challenge/blob/main/README.md_)

The analysis and data processing can be found in `challenge.ipynb`.

In order to reproduce this project I recommend one of the two options listed bellow. 
I have not tested the conda environment in a Windows machine so it might have some issues with system dependencies.   

## Conda environment

If you have conda installed in your machine, clone the repository and run in the repo dir
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
Note that it may take a while to build the image (around 9 minutes) since it has to download everything.

Then run the container with
```shell
docker run -p 8888:8888 --rm vizzuality-challenge
```
Finally you can directly connect to the jupyter lab instance running in the docker by **copying the link displayed in the terminal** into your preferred browser.
