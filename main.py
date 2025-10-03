# main.py
from models import conversion_model, funnel_model, lead_scoring_model

def run_pipeline():
    print("🔹 Running Model 1: Conversion Prediction...")
    conversion_model.run()

    print("\n🔹 Running Model 2: Funnel Stage Prediction...")
    funnel_model.run()

    print("\n🔹 Running Model 3: Lead Scoring...")
    lead_scoring_model.run()

    print("\n✅ Pipeline complete. Predictions saved in the data/ folder.")

if __name__ == "__main__":
    run_pipeline()
