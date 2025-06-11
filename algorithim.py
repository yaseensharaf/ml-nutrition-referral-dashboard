from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import pandas as pd

# Load data
df = pd.read_csv("data\FeedingDashboardData.csv")

# Preprocessing
X = df[['end_tidal_co2','feed_vol','feed_vol_adm','fio2','fio2_ratio','insp_time', 'oxygen_flow_rate','peep','pip', 'resp_rate','sip','tidal_vol','tidal_vol_actual','tidal_vol_kg','tidal_vol_spon', 'bmi']]
y = df['referral']

# Pipeline for imputation, normalization, and model training
pipeline = make_pipeline(
    SimpleImputer(strategy='median'),
    StandardScaler(),
    SVC(probability=True)
)

# Train model on the entire dataset
pipeline.fit(X, y)

# Predict and calculate confidence scores
predicted_referrals = pipeline.predict(X)
probabilities = pipeline.predict_proba(X)
confidence_scores = probabilities.max(axis=1) * 100

# Prepare output
results_df = pd.DataFrame({
    'encounterId': df['encounterId'],
    'Predicted Referral': predicted_referrals,
    'Confidence Score (%)': confidence_scores
})

# Save or display the results
print(results_df)
