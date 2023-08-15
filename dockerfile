# Use the official Python image with version 3.11.4 as base
FROM python:3.11.4

# Set environment variables to ensure Conda doesn't prompt for user interaction
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# Install Conda
RUN apt-get update --fix-missing && \
    apt-get install -y wget bzip2 ca-certificates curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    /bin/bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm -f /tmp/miniconda.sh

ENV PATH /opt/conda/bin:$PATH

# Create and set working directory
RUN mkdir /app
WORKDIR /app

# Copy the Conda environment file
COPY conda_django_sf2gs.yml .

# Create Conda environment
RUN conda env create -f conda_django_sf2gs.yml

# Activate Conda environment
RUN echo "source activate $(head -1 conda_django_sf2gs.yml | cut -d' ' -f2)" > ~/.bashrc

# Copy the Django project into the container
COPY . .

# Expose the port that Django runs on
EXPOSE 8006

# Start Django development server
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8006"]
