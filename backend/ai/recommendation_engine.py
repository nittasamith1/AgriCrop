"""
AgriCrop – Recommendation Engine
Maps disease predictions and soil conditions to actionable
treatment, prevention, and irrigation recommendations.
"""

from typing import Dict, List, Any, Optional


# ── Disease Treatment Database ─────────────────────────────────────────────────
DISEASE_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "Apple___Apple_scab": {
        "treatments": [
            "Apply captan or myclobutanil fungicide at 7–14 day intervals",
            "Prune and destroy infected leaves and twigs",
            "Improve air circulation by thinning the canopy",
        ],
        "prevention": [
            "Choose scab-resistant apple varieties",
            "Remove fallen leaves promptly to reduce overwintering spores",
            "Avoid overhead irrigation",
        ],
        "pesticides": ["Captan 50 WP", "Myclobutanil (Eagle 20EW)", "Mancozeb 75 WP"],
        "organic": ["Sulfur dust", "Neem oil spray"],
    },
    "Apple___Black_rot": {
        "treatments": [
            "Remove all mummified fruit and infected cankers",
            "Apply thiophanate-methyl or captan fungicide",
            "Prune infected branches 8 inches below visible canker",
        ],
        "prevention": [
            "Sanitize pruning tools with bleach solution",
            "Maintain tree vigor with proper fertilization",
            "Avoid wounding bark",
        ],
        "pesticides": ["Thiophanate-methyl", "Captan 50 WP", "Ziram"],
        "organic": ["Bordeaux mixture", "Lime sulfur"],
    },
    "Tomato___Late_blight": {
        "treatments": [
            "Apply chlorothalonil or mancozeb fungicide immediately",
            "Remove and destroy all infected plant material",
            "Avoid working in the garden when plants are wet",
        ],
        "prevention": [
            "Use certified disease-free seed",
            "Practice crop rotation with non-solanaceous crops",
            "Stake or cage tomatoes to improve airflow",
        ],
        "pesticides": ["Chlorothalonil (Bravo 500)", "Mancozeb 75 WP", "Metalaxyl + Mancozeb"],
        "organic": ["Copper-based fungicide", "Compost tea foliar spray"],
    },
    "Tomato___Early_blight": {
        "treatments": [
            "Apply chlorothalonil fungicide at 7–10 day intervals",
            "Remove lower infected leaves to reduce inoculum",
            "Mulch around plants to reduce soil splash",
        ],
        "prevention": [
            "Space plants adequately for airflow",
            "Avoid overhead watering",
            "Remove infected debris at end of season",
        ],
        "pesticides": ["Chlorothalonil", "Mancozeb", "Azoxystrobin (Quadris)"],
        "organic": ["Neem oil", "Copper sulfate spray"],
    },
    "Potato___Late_blight": {
        "treatments": [
            "Apply mancozeb or chlorothalonil at first sign",
            "Destroy severely infected tubers",
            "Hilling soil over potato rows to protect tubers",
        ],
        "prevention": [
            "Plant certified disease-free seed potatoes",
            "Avoid planting in low-lying, poorly drained areas",
            "Scout fields weekly during cool, wet weather",
        ],
        "pesticides": ["Mancozeb 75 WP", "Chlorothalonil 720 SC", "Cymoxanil + Mancozeb"],
        "organic": ["Copper hydroxide", "Bordeaux mixture"],
    },
    "Corn_(maize)___Common_rust_": {
        "treatments": [
            "Apply azoxystrobin or propiconazole fungicide",
            "Scout early and treat at first pustule observation",
        ],
        "prevention": [
            "Plant rust-resistant hybrids",
            "Avoid late planting in high-pressure areas",
        ],
        "pesticides": ["Azoxystrobin (Quadris)", "Propiconazole (Tilt)", "Trifloxystrobin"],
        "organic": ["Sulfur-based fungicides"],
    },
    "default_healthy": {
        "treatments": ["No treatment required. Your crop appears healthy!"],
        "prevention": [
            "Continue regular monitoring every 2 weeks",
            "Maintain proper irrigation and nutrient management",
            "Practice crop rotation each season",
        ],
        "pesticides": [],
        "organic": [],
    },
    "default_disease": {
        "treatments": [
            "Consult your local agricultural extension officer for precise identification",
            "Apply a broad-spectrum fungicide as a precautionary measure",
            "Remove and destroy severely infected plant parts",
        ],
        "prevention": [
            "Maintain proper plant spacing for air circulation",
            "Avoid overhead irrigation; use drip irrigation",
            "Apply organic mulch to reduce soil splash",
            "Practice crop rotation annually",
        ],
        "pesticides": ["Mancozeb 75 WP", "Chlorothalonil 720 SC"],
        "organic": ["Neem oil (5 mL/L)", "Copper-based spray"],
    },
}


# ── Irrigation Recommendation Text ────────────────────────────────────────────

def get_irrigation_recommendation(
    predicted_moisture: float,
    irrigation_recommended: bool,
    irrigation_type: str,
    soil_type: str,
    water_req_mm: float,
) -> str:
    """
    Generate a detailed, human-readable irrigation recommendation.
    """
    if not irrigation_recommended:
        return (
            f"Your soil moisture level is {predicted_moisture:.1f}%, which is adequate. "
            f"No irrigation is needed at this time. Monitor soil moisture daily "
            f"and irrigate when levels drop below the field capacity threshold for {soil_type} soil."
        )

    type_guides = {
        "drip": f"Apply drip irrigation for approximately 2–3 hours, delivering {water_req_mm:.0f}mm of water.",
        "sprinkler": f"Run sprinkler irrigation for 3–4 hours in the early morning. Target: {water_req_mm:.0f}mm.",
        "flood": f"Flood irrigation is recommended. Apply {water_req_mm:.0f}mm of water per hectare.",
        "none": "Monitor moisture levels closely.",
    }

    guide = type_guides.get(irrigation_type, type_guides["drip"])
    return (
        f"⚠️ Soil moisture is {predicted_moisture:.1f}%, below the safe threshold for {soil_type} soil. "
        f"Immediate irrigation is recommended. {guide} "
        f"Re-check soil moisture 24 hours after irrigation."
    )


# ── Disease Recommendation Lookup ─────────────────────────────────────────────

def get_disease_recommendations(disease_class_key: str, is_healthy: bool) -> Dict[str, Any]:
    """
    Return treatment and prevention recommendations for a detected disease.
    Falls back to 'default_healthy' or 'default_disease' if not found.
    """
    if is_healthy:
        return DISEASE_RECOMMENDATIONS["default_healthy"]

    # Try exact match first, then partial match
    if disease_class_key in DISEASE_RECOMMENDATIONS:
        return DISEASE_RECOMMENDATIONS[disease_class_key]

    for key in DISEASE_RECOMMENDATIONS:
        if key in disease_class_key or disease_class_key in key:
            return DISEASE_RECOMMENDATIONS[key]

    return DISEASE_RECOMMENDATIONS["default_disease"]


def get_crop_from_class(class_key: str) -> str:
    """Extract the crop type from a PlantVillage class key."""
    if "___" in class_key:
        return class_key.split("___")[0].replace("_", " ").strip()
    return "Unknown"
