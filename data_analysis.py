import requests
import pandas as pd
from sklearn.preprocessing import LabelEncoder


try:
    users_api = requests.get("http://127.0.0.1:8000/all-users")
    users_api.raise_for_status()
    users_api_data = users_api.json()

    visits_api = requests.get("http://127.0.0.1:8000/all-visits")
    visits_api.raise_for_status()
    visits_api_data = visits_api.json()

    label_encoder = LabelEncoder()

    visits_api_data["visits"] = [
        {("userId" if k == "user_id" else k): v for k, v in visit.items()}
        for visit in visits_api_data["visits"]
    ]

    udf = pd.DataFrame(users_api_data["users"])
    vdf = pd.DataFrame(visits_api_data["visits"])

    merged_df = pd.merge(udf, vdf, on="userId", how="inner")

    merged_df['accepted'] = merged_df['accepted'].fillna(merged_df['accepted'].mode()[0])
    merged_df['status'] = merged_df['status'].fillna('PENDING')

    merged_df['visit_date'] = pd.to_datetime(merged_df['visit_date'], utc=True, errors="coerce")
    merged_df['check_out_date'] = pd.to_datetime(merged_df['check_out_date'], utc=True, errors="coerce")

    merged_df['visit_hour'] = merged_df['visit_date'].dt.hour
    merged_df['visit_hour'] = merged_df["visit_hour"].fillna(12)

    merged_df['visit_session'] = pd.cut(
        merged_df['visit_hour'],
        bins=[0, 6, 12, 18, 24],
        labels=['Night', 'Morning', 'Afternoon', 'Evening'],
        right=False
    )
    merged_df['visit_session'] = merged_df['visit_session'].fillna("Afternoon")

    merged_df['visit_duration'] = (merged_df['check_out_date'] - merged_df['visit_date']).dt.total_seconds()
    merged_df['visit_duration'] = merged_df['visit_duration'].fillna(0)

    merged_df['status_encoded'] = label_encoder.fit_transform(merged_df['status'])

    print(merged_df.shape)

except requests.exceptions.RequestException as e: 
    print(f"Error fetching data from API: {e}")
