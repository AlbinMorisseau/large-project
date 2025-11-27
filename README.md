# Large Project

## Introduction 

This repository contains the work carried out by Albin Morisseau and Emma Lhuillery as part of the Large Project in AI at the University of Klagenfurt between October 2025 and February 2026

The aim of this project is to study the behaviors and the needs of travellers with specific needs (disabilities, pets, young children) who require special arrangements and conditions.

## Hardware

We ran the code using this laptop hardware:
- RTX4070 GPU / 8 Go RAM
- Intel Core I9 CPU / 32 Go RAM

NB: We strongly recommend using hardware or cloud services to significantly speed up calculation times.

## Project Structure
```
large project/
├── data/
|   ├── original/
│   └── processed/
├── notebooks/
|   ├── eda/ 
|   └── draft/
├── src/  
├── .gitignore
├── requirements.txt
└── README.md
```

## Project set up

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/AlbinMorisseau/large-project.git](https://github.com/AlbinMorisseau/large-project.git)
    cd large project
    ```
2.  **Create and activate a virtual envrionment:**
    ```bash
    python -m venv venv
    # For Windows
    .\venv\Scripts\activate
    # For MacOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependancies:**
    ```bash
    pip install -r requirements.txt
    ```

## Datasets Used

This project uses a wide range of publicly available review datasets covering hotels, restaurants, airlines, activities, and social media.  
Below is the complete list of datasets:

- **Booking.com Accommodation Reviews**  
  https://huggingface.co/datasets/Booking-com/accommodation-reviews/tree/main

- **Yelp Open Dataset**  
  https://business.yelp.com/data/resources/open-dataset/

- **Hotel Reviews 1 / 2 / 3 (Datafiniti)**  
  https://www.kaggle.com/datasets/datafiniti/hotel-reviews

- **TripAdvisor Hotel Reviews**  
  https://www.kaggle.com/datasets/joebeachcapital/hotel-reviews?select=reviews.csv

- **Twitter Reviews Dataset**  
  https://www.kaggle.com/datasets/goyaladi/twitter-dataset?select=twitter_dataset.csv

- **Airline Reviews (Dataset 1)**  
  https://www.kaggle.com/datasets/chaudharyanshul/airline-reviews

- **Airline Reviews (Dataset 2)**  
  https://www.kaggle.com/datasets/sujalsuthar/airlines-reviews

- **European Hotel Reviews (515k)**  
  https://www.kaggle.com/datasets/jiashenliu/515k-hotel-reviews-data-in-europe

- **Restaurant Reviews (Dataset 1)**  
  https://www.kaggle.com/datasets/d4rklucif3r/restaurant-reviews

- **Restaurant Reviews (Dataset 2)**  
  https://www.kaggle.com/datasets/joebeachcapital/restaurant-reviews

- **Activities Reviews**  
  https://www.kaggle.com/datasets/johnwdata/reviewsactivities

- **European Restaurant Reviews**  
  https://www.kaggle.com/datasets/gorororororo23/european-restaurant-reviews

