# 1. Business Understanding 'Classification of Zambian Parliamentary Questions Order Papers.'
## Problem Statement
Each time there is a parliamentary session, the Zambian National Assembly releases Order Papers that include a large number of questions from members of parliament. These enquiries are usually divided into two categories, kind (written, oral, urgent) and subject (agriculture, education, health). However, the existing method of recognising and categorising these issues is labour intensive, manual, and prone to errors. This makes it challenging for interested parties like scholars, journalists, and the general public to find and evaluate questions of interest in a timely manner. Therefore, an automated system that can correctly categorise Order Paper questions into their respective types and subject categories based on their textual content is required. This will allow for better data driven insights into parliamentary activities, faster information retrieval, and increased transparency.
This project seeks to develop this same automated system to classify parliamentary questions in Zambia’s Order Papers by type and subject, addressing the inefficiencies and inconsistencies of manual categorisation to improve accessibility, transparency, and analysis of legislative activities.

## Business Objectives
From a real world perspective, the business objectives this project aims to achieve are:

* Improved Information Accessibility:- which allows MPs, journalists, researchers, and the public to quickly find relevant questions by category or ministry.

* Enhanced Parliamentary Transparency:- provide clear, structured and searchable parliamentary records to promote openness and accountability.

* Automate Question Classification:- remove manual sorting of order paper questions by developing an automated classification tool.

* Enable Data-driven Insights:- to see which ministries receive the most questions and support analysis in parliamentary questioning.

## Data Mining Goals
1. To build a classification model to automatically categorize parliamentary questions from Zambia's Order Papers into their respective types (written, oral, urgent) and subject categories (such as agriculture, education, health) based on their textual content.
2. To design a model that improves the accuracy and efficiency of categorization of older papers, reducing manual labor and minimizing errors.
3. To use natural language processing (NLP) techniques to extract meaningful features from the text of the questions to enhance classification performance.
4. To facilitate faster information retrieval, better data-driven insights into parliamentary activities, and improve accessibility and transparency for scholars, journalists, and the general public.
5. To develop text cleaning and feature extraction workflows (e.g., TF-IDF, embeddings) to transform raw parliamentary question text into structured inputs for classification models.

## Project success criteria( done by @Kahyatadksn & @Leonard)
### 1. Model Performance & Accuracy

Data Availability: The model must provide users with access to a minimum of 1,000 labelled questions.
Data Accuracy: The accessible questions must have an accuracy rate of at least 80%.

### 2. Filtering & User Functionality Search & Filtering:
The system must allow users to filter questions based on the following criteria:

1. Year

1. Member of Parliament's name

1. Constituency

1. Chiefdom

1. District

1. Ward

1. Keywords (e.g., ministry names, FISP, budget, CDF, bills, motions)

1. Timeframe (start and end date)

* Filtering Accuracy: The results from these filtering operations must be accurate at a rate of at least 80%.
Output & Usability.

* Export Formats: The system must be able to export user-generated outputs in both CSV and PDF formats.

* Data Quality: The exported data must be clean and correctly set up, allowing users to analyze it without difficulty.

