# OneNews Weather

OneNews Weather is an accuracy-first weather intelligence platform being developed as part of the OneNews ecosystem (1news.co).

The goal is to build a next-generation weather backend that dynamically determines the most accurate forecast sources for a given location, forecast horizon, and weather regime — and blends them intelligently to outperform traditional consumer weather providers.

This repository focuses exclusively on the **backend foundation**: data ingestion, normalization, evaluation, and machine learning infrastructure. UI and mobile applications will be built later on top of stable APIs.

---

## Core Principles

- **Accuracy over aesthetics**
- **Evidence-driven forecasting**
- **Per-location intelligence, not global averages**
- **Open data and open-source tooling**
- **Scientific rigor and continuous evaluation**

---

## Phase 1 Scope (Current)

- **Geography:** United States (CONUS only)
- **Variables:** Temperature (initial focus)
- **Forecast Horizons:**  
  - Nowcast (0–1h)  
  - Short-term (1–6h)  
  - Daily (6–48h)  
- **Forecast Sources:**  
  - GFS  
  - HRRR  
  - NAM  
- **Observations / Ground Truth:**  
  - METAR / ASOS surface stations
- **Spatial Indexing:**  
  - H3 hexagonal grid
- **ML Usage:**  
  - Evaluation-first  
  - Source selection models before blending  
  - No neural networks in initial phase

---

## High-Level Architecture

1. **Data Ingestion**
   - Fetch raw forecast model outputs and observational data
   - Store immutable raw data for reproducibility

2. **Normalization & Regridding**
   - Convert heterogeneous model grids into a unified H3-based spatial index
   - Align temporal resolutions across sources

3. **Evaluation Engine**
   - Score forecast accuracy against observations per:
     - H3 cell
     - Forecast horizon
     - Time of year
   - Produce per-source performance profiles

4. **Machine Learning (Later Phases)**
   - Classifiers to predict best-performing sources per context
   - Dynamic forecast blending based on learned weights

5. **API Layer**
   - Internal APIs for forecast retrieval and analysis
   - Designed to support web and mobile clients in the future

---

## Repository Structure

