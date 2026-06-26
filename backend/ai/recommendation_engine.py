"""
AgriCrop – Recommendation Engine
Provides disease treatments, prevention tips, and irrigation recommendations.
"""

from typing import Dict, List, Any

# Disease recommendations database
DISEASE_DATABASE = {
    "Apple_scab": {
        "treatments": [
            "Apply sulfur-based fungicides every 10-14 days",
            "Use copper fungicides during dormant season",
            "Remove infected leaves and fallen fruit",
        ],
        "prevention": [
            "Prune to improve air circulation",
            "Avoid overhead watering",
            "Use resistant apple varieties",
            "Apply mulch to prevent spore spread",
        ],
        "pesticides": [
            "Sulfur dust",
            "Copper sulfate",
            "Captan fungicide",
            "Myclobutanil",
        ],
        "organic": [
            "Neem oil spray",
            "Baking soda solution (1 tbsp/gallon water)",
            "Milk spray (1 part milk to 9 parts water)",
        ],
    },
    "Potato_early_blight": {
        "treatments": [
            "Apply mancozeb fungicide weekly",
            "Use copper-based fungicides",
            "Remove infected leaves immediately",
            "Increase spacing for air circulation",
        ],
        "prevention": [
            "Use certified disease-free seed potatoes",
            "Rotate crops (avoid growing in same field for 2 years)",
            "Remove volunteer potato plants",
            "Manage weeds",
        ],
        "pesticides": [
            "Mancozeb",
            "Chlorothalonil",
            "Copper fungicide",
            "Azoxystrobin",
        ],
        "organic": [
            "Bacillus subtilis spray",
            "Sulfur powder",
            "Lime sulfur spray",
            "Trichoderma harzianum",
        ],
    },
    "Tomato_early_blight": {
        "treatments": [
            "Remove infected lower leaves",
            "Apply chlorothalonil fungicide",
            "Space plants for good air flow",
            "Use drip irrigation to keep leaves dry",
        ],
        "prevention": [
            "Mulch to prevent soil splash",
            "Stake or trellis plants",
            "Remove bottom leaves",
            "Avoid working in wet plants",
        ],
        "pesticides": [
            "Chlorothalonil",
            "Mancozeb",
            "Copper fungicide",
            "Azoxystrobin",
        ],
        "organic": [
            "Bacillus subtilis",
            "Copper sulfate",
            "Sulfur powder",
            "Neem oil",
        ],
    },
    "Tomato_late_blight": {
        "treatments": [
            "Apply mancozeb or copper fungicide immediately",
            "Remove infected plants if severe",
            "Increase air circulation",
            "Remove infected foliage",
        ],
        "prevention": [
            "Plant resistant varieties",
            "Ensure good drainage",
            "Avoid overhead watering",
            "Rotate crops",
        ],
        "pesticides": [
            "Mancozeb",
            "Chlorothalonil",
            "Copper hydroxide",
            "Metalaxyl + Mancozeb",
        ],
        "organic": [
            "Bacillus subtilis",
            "Copper fungicide",
            "Lime sulfur",
            "Potassium bicarbonate",
        ],
    },
    "Healthy": {
        "treatments": [
            "Continue regular monitoring",
            "Maintain good cultural practices",
            "Ensure adequate water and nutrients",
        ],
        "prevention": [
            "Regular inspection of plants",
            "Proper spacing for air circulation",
            "Consistent watering schedule",
            "Balanced fertilization",
        ],
        "pesticides": [
            "No treatment needed - plant is healthy",
        ],
        "organic": [
            "Maintain organic practices",
            "Use compost for soil health",
            "Encourage beneficial insects",
        ],
    },
}

# Crop classification from disease class
CROP_MAPPING = {
    "apple": "Apple",
    "blueberry": "Blueberry",
    "cherry": "Cherry",
    "corn": "Corn",
    "grape": "Grape",
    "orange": "Orange",
    "peach": "Peach",
    "pepper": "Pepper",
    "potato": "Potato",
    "raspberry": "Raspberry",
    "soybean": "Soybean",
    "squash": "Squash",
    "strawberry": "Strawberry",
    "tomato": "Tomato",
}

# Irrigation recommendations by soil moisture
IRRIGATION_RECOMMENDATIONS = {
    "critical": {
        "message": "Immediate irrigation needed - soil is critically dry",
        "days": 0,
        "frequency": "Daily",
    },
    "urgent": {
        "message": "Water plants within 24 hours",
        "days": 1,
        "frequency": "Every 2 days",
    },
    "soon": {
        "message": "Plan watering for next 2-3 days",
        "days": 2,
        "frequency": "Every 3-4 days",
    },
    "normal": {
        "message": "Current moisture levels are adequate",
        "days": 4,
        "frequency": "Weekly",
    },
    "adequate": {
        "message": "Soil moisture is sufficient. Avoid overwatering.",
        "days": 5,
        "frequency": "As needed",
    },
}


def get_disease_recommendations(
    disease_class_key: str,
    is_healthy: bool = False,
) -> Dict[str, Any]:
    """
    Get disease recommendations, treatments, and pesticide info.
    
    Args:
        disease_class_key: Disease class identifier (e.g., "Tomato___Early_blight")
        is_healthy: Whether the crop is healthy
    
    Returns:
        Dict with treatments, prevention tips, pesticides, and organic alternatives
    """
    if is_healthy:
        return DISEASE_DATABASE.get("Healthy", DISEASE_DATABASE["Healthy"])

    # Extract disease name from class key
    disease_name = disease_class_key.replace("___", "_").split("_", 1)[-1]
    
    # Try to find matching disease in database
    for key, value in DISEASE_DATABASE.items():
        if key.lower() in disease_name.lower():
            return value

    # Fallback: return generic recommendations
    return {
        "treatments": [
            "Consult local agricultural extension services",
            "Monitor plant closely",
            "Remove severely infected plants",
        ],
        "prevention": [
            "Maintain good cultural practices",
            "Ensure adequate spacing",
            "Regular monitoring",
        ],
        "pesticides": [
            "Consult with agricultural extension or plant pathologist",
        ],
        "organic": [
            "Use cultural control methods",
            "Remove affected plant parts",
            "Encourage beneficial insects",
        ],
    }


def get_crop_from_class(disease_class_key: str) -> str:
    """
    Extract crop name from disease class key.
    
    Args:
        disease_class_key: e.g., "Tomato___Early_blight"
    
    Returns:
        Crop name (e.g., "Tomato")
    """
    parts = disease_class_key.split("___")
    if parts:
        crop_prefix = parts[0].replace("(", "").replace(")", "").split()[0].lower()
        for key, val in CROP_MAPPING.items():
            if key in crop_prefix:
                return val
    return "Unknown Crop"


def get_irrigation_recommendation(
    predicted_moisture: float,
) -> Dict[str, Any]:
    """
    Get irrigation recommendation based on predicted soil moisture.
    
    Args:
        predicted_moisture: Soil moisture percentage (0-100)
    
    Returns:
        Dict with recommendation, urgency, and next watering schedule
    """
    if predicted_moisture < 20:
        recommendation = IRRIGATION_RECOMMENDATIONS["critical"]
    elif predicted_moisture < 30:
        recommendation = IRRIGATION_RECOMMENDATIONS["urgent"]
    elif predicted_moisture < 40:
        recommendation = IRRIGATION_RECOMMENDATIONS["soon"]
    elif predicted_moisture < 60:
        recommendation = IRRIGATION_RECOMMENDATIONS["normal"]
    else:
        recommendation = IRRIGATION_RECOMMENDATIONS["adequate"]

    return {
        "message": recommendation["message"],
        "next_watering_days": recommendation["days"],
        "irrigation_frequency": recommendation["frequency"],
        "moisture_level": predicted_moisture,
        "urgency": list(IRRIGATION_RECOMMENDATIONS.keys())[
            list(IRRIGATION_RECOMMENDATIONS.values()).index(recommendation)
        ],
    }


def get_treatment_timeline(disease_name: str) -> List[Dict[str, Any]]:
    """
    Get a treatment timeline/schedule for a disease.
    """
    return [
        {
            "week": 1,
            "action": "Identify and isolate affected plants",
            "priority": "High",
        },
        {
            "week": 2,
            "action": "Begin fungicide application",
            "priority": "High",
        },
        {
            "week": 3,
            "action": "Continue treatment, monitor progress",
            "priority": "Medium",
        },
        {
            "week": 4,
            "action": "Evaluate treatment effectiveness",
            "priority": "High",
        },
        {
            "week": 5,
            "action": "Implement preventive measures",
            "priority": "Medium",
        },
    ]
