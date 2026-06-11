# DustWatch

DustWatch is a geospatial machine learning and web application project designed to detect and monitor likely construction activity using satellite imagery. The system uses Google Earth Engine for geospatial data processing, a machine learning pipeline to identify construction patches, and a web interface for visualization.

## Architecture Overview

The repository is structured into three primary components:

* Data Pipeline: A Python based geospatial machine learning pipeline that extracts data from Google Earth Engine, creates labeled patches, trains a Random Forest model, and generates GeoJSON outputs of detected construction sites. Located in the `data-pipeline` directory.
* Backend Service: A FastAPI application providing the REST API for the frontend. It integrates with Google Earth Engine and serves the processed geospatial data. Located in the `scripts/apps/backend` directory.
* Frontend Application: A React single page application built with Vite, TypeScript, and Leaflet. It provides a map based interface to visualize the output of the data pipeline and interact with the backend service. Located in the `scripts/apps/frontend` directory.

## Repository Structure

* `data-pipeline/`: Machine learning pipeline scripts, including change detection, patch extraction, model training, and GeoJSON generation. Contains its own detailed README.
* `scripts/apps/backend/`: Source code for the backend API server.
* `scripts/apps/frontend/`: Source code for the user interface.

## Prerequisites

To run this project locally, ensure the following software is installed:

* Python 3.10 or higher
* Node.js 18 or higher
* Google Cloud account with Earth Engine API enabled

## Setup and Installation

### 1. Python Environment

Both the data pipeline and the backend service share a Python environment. It is recommended to use a virtual environment.

Create and activate a virtual environment at the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install the required Python dependencies:

```powershell
pip install -r scripts\apps\backend\requirements.txt
```

### 2. Node Environment

Navigate to the frontend directory and install the required Node.js dependencies:

```powershell
cd scripts\apps\frontend
npm install
```

## Configuration

The project requires authentication with Google Earth Engine. You must provide a valid Google Cloud Project ID.

Create a `.env` file in the `scripts/apps/backend` directory:

```env
GEE_PROJECT_ID=your_google_cloud_project_id
```

## Usage Guidelines

### Data Pipeline

The data pipeline scripts are designed to be executed sequentially from the repository root. Please refer to `data-pipeline/README.md` for specific execution steps.

Example command to start the change detection process:

```powershell
.\.venv\Scripts\python.exe data-pipeline\change_detection.py
```

### Backend Server

The FastAPI backend must be running to serve data to the frontend application.

Start the backend server:

```powershell
cd scripts\apps\backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend Application

To launch the web interface, start the Vite development server.

Start the frontend server:

```powershell
cd scripts\apps\frontend
npm run dev
```

The web application will be accessible at `http://localhost:5173`.

## Data Management and Version Control

Generated data artifacts, including `.tif` rasters, `.npy` arrays, compiled `.pkl` models, and localized `node_modules` are excluded from version control via `.gitignore`. Ensure that raw or processed datasets remain local to your development environment.
