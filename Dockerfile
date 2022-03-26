FROM continuumio/miniconda3

WORKDIR challenge

COPY environment.yml data_downloader.py challenge.ipynb ./
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "vizzuality", "/bin/bash", "-c"]

RUN ["conda", "run", "--no-capture-output", "-n", "vizzuality", "python", "data_downloader.py", "-f", "data"]

EXPOSE 8888
ENTRYPOINT ["conda", "run","--no-capture-output", "-n", "vizzuality", "jupyter", "lab","--ip=0.0.0.0","--allow-root"]
