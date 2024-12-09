import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from windrose import WindroseAxes
import streamlit as st
from scipy.stats import zscore

DATA_SOURCES = {
    "Benin Malanville": "data/benin-malanville.csv",
    "Sierra Leone Bumbuna": "data/sierraleone-bumbuna.csv",
    "Togo Dapaong QC": "data/togo-dapaong_qc.csv",
}

@st.cache_data
def load_file(file_path):
    return pd.read_csv(file_path)

@st.cache_data
def preprocess_data(dataframe):
    if 'Datetime' in dataframe.columns:
        dataframe['Datetime'] = pd.to_datetime(dataframe['Datetime'], errors='coerce')
        dataframe.dropna(subset=['Datetime'], inplace=True)
    dataframe.ffill(inplace=True)
    dataframe.bfill(inplace=True)
    dataframe.dropna(inplace=True)
    dataframe.drop_duplicates(inplace=True)
    numeric_cols = dataframe.select_dtypes(include=['number'])
    if not numeric_cols.empty:
        z_scores = numeric_cols.apply(zscore)
        dataframe = dataframe[(z_scores.abs() <= 3).all(axis=1)]
    dataframe.reset_index(drop=True, inplace=True)
    return dataframe

all_datasets = {name: preprocess_data(load_file(path)) for name, path in DATA_SOURCES.items()}

selected_location = st.sidebar.selectbox("Choose Location", list(DATA_SOURCES.keys()))
chosen_dataset = all_datasets.get(selected_location, pd.DataFrame())

st.title(f"Environmental Monitoring Dashboard for {selected_location}")

sections = ["Summary", "Data Insights", "Charts", "Advanced Metrics"]
active_section = st.sidebar.radio("Select Section", sections)

if active_section == "Summary":
    st.header("Location Overview")
    st.write(f"This dashboard provides a comprehensive analysis of the dataset for {selected_location}. Explore the sections for insights, visualizations, and metrics.")

elif active_section == "Data Insights":
    st.header("Data Insights")
    st.write("Statistical Overview:")
    st.write(chosen_dataset.describe())
    st.write("Missing Data Overview:")
    st.write(chosen_dataset.isnull().sum())
    st.write("Duplicate Records:")
    st.write(chosen_dataset.duplicated().sum())

elif active_section == "Charts":
    st.header("Data Visualizations")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(chosen_dataset.corr(), annot=True, cmap="coolwarm", ax=ax)
    plt.title("Correlation Matrix")
    st.pyplot(fig)

    if 'Timestamp' in chosen_dataset.columns:
        chosen_dataset['Timestamp'] = pd.to_datetime(chosen_dataset['Timestamp'])
        chosen_dataset.set_index('Timestamp', inplace=True)
        fig, ax = plt.subplots(figsize=(10, 5))
        chosen_dataset[['GHI', 'DNI', 'DHI', 'Tamb']].plot(ax=ax)
        plt.title("Time Series Trends: GHI, DNI, DHI, Tamb")
        st.pyplot(fig)

elif active_section == "Advanced Metrics":
    st.header("Advanced Metrics")
    fig, ax = plt.subplots()
    sns.scatterplot(x="Tamb", y="RH", data=chosen_dataset, alpha=0.7, ax=ax)
    plt.title("Temperature vs. Relative Humidity")
    st.pyplot(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    chosen_dataset[['TModA', 'TModB', 'Tamb']].plot(ax=ax)
    plt.title("Module Temperature Trends")
    st.pyplot(fig)

    if 'WD' in chosen_dataset.columns and 'WS' in chosen_dataset.columns:
        ax = WindroseAxes.from_ax()
        ax.bar(chosen_dataset['WD'], chosen_dataset['WS'], normed=True, opening=0.8, edgecolor="black")
        ax.set_title("Wind Rose: Speed vs. Direction")
        ax.set_legend()
        st.pyplot(ax.figure)

    fig, ax = plt.subplots()
    sns.histplot(chosen_dataset['WD'], kde=True, bins=36, ax=ax)
    plt.title("Wind Direction Distribution")
    st.pyplot(fig)

    analysis_columns = ['GHI', 'DNI', 'DHI', 'Tamb', 'RH', 'WS']
    available_columns = [col for col in analysis_columns if col in chosen_dataset.columns]
    if available_columns:
        sns.pairplot(chosen_dataset[available_columns])
        st.pyplot()