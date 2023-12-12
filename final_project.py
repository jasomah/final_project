# -*- coding: utf-8 -*-
"""final project

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1H-UkUlqrRUCniRiPJw5g7wQCkBDsYhmf
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
import streamlit as st
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt

# Load the data
#df = pd.read_csv(r"C:\Users\asoma\OneDrive\Dokumente\Uni\Master\NCSU\Fall 2023\Analytics - From Data to Decisions\final project\kaggle_survey_2022_responses.csv", skiprows=1)
df = pd.read_csv(r"C:\Users\asoma\OneDrive\Dokumente\Uni\Master\NCSU\Fall 2023\Analytics - From Data to Decisions\final project\kaggle_survey_2022_responses.csv", skiprows=1)

# Function to preprocess salary range
def preprocess_salary_range(salary_range):
    try:
        return float(salary_range)
    except ValueError:
        try:
            lower, upper = map(float, salary_range.replace('$', '').replace(',', '').split('-'))
            return (lower + upper) / 2
        except ValueError:
            return np.nan

# Apply preprocessing to the salary column
df['What is your current yearly compensation (approximate $USD)?'] = df['What is your current yearly compensation (approximate $USD)?'].apply(preprocess_salary_range)

# Drop rows with missing salary values
df = df.dropna(subset=['What is your current yearly compensation (approximate $USD)?'])

# Extract features and target variable
y = df['What is your current yearly compensation (approximate $USD)?']
X = df.drop(['What is your current yearly compensation (approximate $USD)?'], axis=1)

# Split the data
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

# Define numeric and categorical features
numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
categorical_features = X.select_dtypes(include=[object]).columns.tolist()

# Create transformers for numeric and categorical features
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))
])

# Combine transformers into a ColumnTransformer
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ],
    remainder='passthrough'
)

# Create an XGBoost model
model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)

# Create a pipeline with preprocessing and modeling steps
pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                             ('model', model)])

# Cross-validate the model
cv_scores = cross_val_score(pipeline, x_train, y_train, cv=5, scoring='neg_mean_squared_error')
print(f"Cross-validated RMSE: {-np.mean(cv_scores)**0.5}")

# Fit the pipeline on the training data
pipeline.fit(x_train, y_train)

# Streamlit App
st.title("Income Prediction")

# Define columns for the app input
app_input_columns = ['What is your age (# years)?', 'What is your gender? - Selected Choice', 'In which country do you currently reside?',
                     'Are you currently a student? (high school, university, or graduate)',
                     'For how many years have you been writing code and/or programming?']

# Extract relevant columns for the app input from the training data
x_train_app = x_train[app_input_columns]

# Streamlit app input widgets within a form
with st.form("prediction_form"):
    # Streamlit app input widgets
    age = st.slider('Age', min_value=18, max_value=80, value=25)
    gender = st.selectbox('Gender', ['Male', 'Female', 'Other'])
    country = st.selectbox('Country', x_train_app['In which country do you currently reside?'].unique())
    education_options = ['Yes', 'No']
    education = st.selectbox('Education Level', education_options, index=education_options.index('No'))
    experience = st.slider('Coding Experience (Years)', min_value=0, max_value=30, value=5)


    # Button to trigger prediction
    submitted = st.form_submit_button("Predict Salary")

    # Code to run after the form is submitted
    if submitted:
        # Create input_data DataFrame for prediction
        input_data = pd.DataFrame({
            'Age': [age],
            'Gender': [gender],
            'In which country do you currently reside?': [country],
            'Are you currently a student? (high school, university, or graduate)': [education],
            'For how many years have you been writing code and/or programming?': [experience],
        })

        # Ensure that input_data has all the necessary columns
        input_data = pd.concat([pd.DataFrame(columns=x_train.columns), input_data], ignore_index=True)

        # Make predictions using the pipeline
        prediction = pipeline.predict(input_data)

        # Display the predicted salary range
        st.subheader('Predicted Salary')
        st.write(f"${prediction[0]:,.2f}")

        # Fit the pipeline on the training data
        pipeline.fit(x_train, y_train)

        # Make predictions using the pipeline
        prediction = pipeline.predict(x_test)

        prediction_test = pipeline.predict(x_test)

        # Calculate R-squared score
        r2_value_test = r2_score(y_test, prediction_test)

        # Display the R-squared score
        st.subheader('R-squared Score on Test Data')
        st.write(f"R-squared Score: {r2_value_test:.2f}")

        # Get booster from the pipeline
        booster = pipeline.named_steps['model'].get_booster()
        # Get feature importance
        feature_importance = booster.get_score(importance_type='weight')
    
       