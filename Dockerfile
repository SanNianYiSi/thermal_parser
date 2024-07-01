# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.9-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    libgomp1 \
    exiftool \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire contents of the local directory to the working directory in the container
COPY . .

# Ensure that the necessary directories exist
RUN mkdir -p plugins/dji_thermal_sdk_v1.5_20240507

# Copy the necessary plugin files into the container
COPY plugins/ plugins/

# Run the setup.py to install the package
# RUN pip install setup.py
RUN pip install .

# Command to run your application or start an interactive shell
CMD ["python"]