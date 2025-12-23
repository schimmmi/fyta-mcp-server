"""
Plant Context and Knowledge System

Stores plant-specific context that FYTA doesn't know:
- Substrate type (mineral, organic, hydro, lechuza-pon, etc.)
- Container type (pot, lechuza, hydroponic, etc.)
- Growth phase (seedling, vegetative, flowering, dormant)
- Special care requirements

Enables context-aware recommendations that understand YOUR setup.
"""
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class PlantContextStore:
    """Storage for plant context information"""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            home = Path.home()
            storage_dir = home / ".fyta_mcp"
            storage_dir.mkdir(exist_ok=True)
            self.storage_path = storage_dir / "plant_contexts.json"
        else:
            self.storage_path = Path(storage_path)

        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure storage file exists"""
        if not self.storage_path.exists():
            self.storage_path.write_text(json.dumps({"contexts": {}}, indent=2))

    def _load_contexts(self) -> Dict:
        """Load all plant contexts"""
        try:
            data = json.loads(self.storage_path.read_text())
            return data.get("contexts", {})
        except Exception:
            return {}

    def _save_contexts(self, contexts: Dict):
        """Save all plant contexts"""
        self.storage_path.write_text(json.dumps({"contexts": contexts}, indent=2))

    def set_context(self, plant_id: int, context: Dict) -> Dict:
        """
        Set or update context for a plant

        Args:
            plant_id: Plant ID
            context: Context dictionary

        Returns:
            Updated full context
        """
        contexts = self._load_contexts()

        plant_key = str(plant_id)
        if plant_key not in contexts:
            contexts[plant_key] = {}

        # Update context
        contexts[plant_key].update(context)
        contexts[plant_key]["last_updated"] = datetime.now().isoformat()

        self._save_contexts(contexts)

        return contexts[plant_key]

    def get_context(self, plant_id: int) -> Optional[Dict]:
        """Get context for a plant"""
        contexts = self._load_contexts()
        return contexts.get(str(plant_id))

    def delete_context(self, plant_id: int) -> bool:
        """Delete context for a plant"""
        contexts = self._load_contexts()
        plant_key = str(plant_id)

        if plant_key in contexts:
            del contexts[plant_key]
            self._save_contexts(contexts)
            return True
        return False


# Knowledge base for context-aware recommendations
SUBSTRATE_KNOWLEDGE = {
    "mineral": {
        "description": "Mineral substrate (perlite, pumice, lava, zeolite)",
        "water_retention": "low",
        "drainage": "excellent",
        "fertilizer_needs": "high",
        "recommendations": {
            "watering": "Water more frequently than organic soil. Check moisture sensor daily.",
            "fertilizing": "Fertilize with every watering at 1/4 strength, or weekly at full strength.",
            "monitoring": "Mineral substrates dry quickly. Set aggressive watering reminders."
        }
    },
    "organic": {
        "description": "Traditional potting soil with peat, compost, bark",
        "water_retention": "medium",
        "drainage": "good",
        "fertilizer_needs": "medium",
        "recommendations": {
            "watering": "Water when top 2-3cm of soil is dry. Standard watering schedule.",
            "fertilizing": "Fertilize every 2-4 weeks during growing season.",
            "monitoring": "Standard care applies. Follow FYTA sensor recommendations."
        }
    },
    "lechuza_pon": {
        "description": "Lechuza-PON mineral substrate (zeolite, lava, pumice, fertilizer)",
        "water_retention": "medium",
        "drainage": "excellent",
        "fertilizer_needs": "low",
        "recommendations": {
            "watering": "Keep reservoir filled. PON wicks water from bottom. Never top-water heavily.",
            "fertilizing": "PON contains slow-release fertilizer. Only add liquid fertilizer every 2-3 months.",
            "monitoring": "Sensor may show 'low moisture' at top - this is normal! Check reservoir level instead."
        }
    },
    "hydroponic": {
        "description": "Soilless hydroponic system (water culture, NFT, DWC)",
        "water_retention": "high",
        "drainage": "n/a",
        "fertilizer_needs": "high",
        "recommendations": {
            "watering": "Maintain proper water level. Check pH and EC daily.",
            "fertilizing": "Use hydroponic nutrients continuously. Monitor EC: 1.2-2.0 mS/cm.",
            "monitoring": "FYTA sensors not designed for hydro. Use EC/pH meters instead."
        }
    },
    "semi_hydro": {
        "description": "Semi-hydroponics (LECA, clay pebbles with reservoir)",
        "water_retention": "low_to_medium",
        "drainage": "excellent",
        "fertilizer_needs": "high",
        "recommendations": {
            "watering": "Keep water level at 1/4 to 1/3 of pot height. Let dry between refills.",
            "fertilizing": "Add nutrients with every water change. Use hydroponic or liquid fertilizer.",
            "monitoring": "Sensor should be in LECA zone, not water reservoir."
        }
    }
}

CONTAINER_KNOWLEDGE = {
    "lechuza": {
        "description": "Self-watering Lechuza planter with reservoir",
        "features": ["water_reservoir", "bottom_watering", "water_level_indicator"],
        "recommendations": {
            "setup": "Use with Lechuza-PON for best results. Ensure wick reaches reservoir.",
            "watering": "Fill reservoir only. Never water from top after establishment.",
            "monitoring": "Check water indicator, not just sensor. Reservoir can last 1-2 weeks."
        }
    },
    "self_watering": {
        "description": "Generic self-watering pot with reservoir",
        "features": ["water_reservoir", "wicking_system"],
        "recommendations": {
            "setup": "Ensure wicking material (rope, mat) connects soil to reservoir.",
            "watering": "Fill reservoir. Top-water occasionally to prevent salt buildup.",
            "monitoring": "Sensor may not detect reservoir water. Check physically."
        }
    },
    "terracotta": {
        "description": "Unglazed clay pot",
        "features": ["breathable", "evaporative_cooling", "fast_drying"],
        "recommendations": {
            "watering": "Dries faster than plastic. Water more frequently.",
            "monitoring": "Expect faster moisture drop. Adjust thresholds accordingly."
        }
    },
    "plastic": {
        "description": "Standard plastic nursery pot",
        "features": ["water_retentive", "lightweight"],
        "recommendations": {
            "watering": "Standard watering. Ensure drainage holes exist.",
            "monitoring": "Standard sensor interpretation applies."
        }
    }
}

GROWTH_PHASE_KNOWLEDGE = {
    "seedling": {
        "description": "Young plant, first true leaves",
        "water_needs": "high_frequency_low_amount",
        "light_needs": "moderate_to_high",
        "fertilizer_needs": "very_low",
        "recommendations": {
            "watering": "Keep consistently moist but not soggy. Water lightly and frequently.",
            "lighting": "Provide 14-16 hours light. Seedlings stretch if insufficient light.",
            "fertilizing": "No fertilizer for first 2-3 weeks. Then 1/4 strength only."
        }
    },
    "vegetative": {
        "description": "Active growth phase, producing leaves/stems",
        "water_needs": "high",
        "light_needs": "high",
        "fertilizer_needs": "high",
        "recommendations": {
            "watering": "Water thoroughly when top soil dries. Plant is actively growing.",
            "lighting": "Provide 14-18 hours light for maximum growth.",
            "fertilizing": "Fertilize regularly (weekly). Use nitrogen-rich fertilizer."
        }
    },
    "flowering": {
        "description": "Reproductive phase, producing flowers/fruit",
        "water_needs": "very_high",
        "light_needs": "very_high",
        "fertilizer_needs": "high_phosphorus",
        "recommendations": {
            "watering": "Increase watering frequency. Flowering plants are thirsty!",
            "lighting": "12 hours for short-day plants, 14-16 for long-day plants.",
            "fertilizing": "Switch to bloom fertilizer (high phosphorus/potassium, lower nitrogen)."
        }
    },
    "fruiting": {
        "description": "Producing fruits/seeds",
        "water_needs": "very_high",
        "light_needs": "high",
        "fertilizer_needs": "high_potassium",
        "recommendations": {
            "watering": "Consistent watering critical. Irregular watering causes fruit splitting.",
            "lighting": "Maintain high light for fruit development.",
            "fertilizing": "High potassium for fruit quality. Reduce nitrogen."
        }
    },
    "dormant": {
        "description": "Winter dormancy, minimal growth",
        "water_needs": "low",
        "light_needs": "low_to_moderate",
        "fertilizer_needs": "none",
        "recommendations": {
            "watering": "Reduce watering significantly. Let soil dry more between waterings.",
            "lighting": "Natural daylight is sufficient. Some plants need cool period.",
            "fertilizing": "NO fertilizer during dormancy. Resume in spring."
        }
    }
}


def get_context_aware_recommendations(plant_data: Dict, context: Optional[Dict]) -> List[Dict]:
    """
    Generate context-aware recommendations

    Args:
        plant_data: Current plant sensor data
        context: Plant context

    Returns:
        List of context-aware recommendations
    """
    if not context:
        return []

    recommendations = []

    substrate = context.get("substrate")
    container = context.get("container")
    growth_phase = context.get("growth_phase")

    # Substrate-specific recommendations
    if substrate and substrate in SUBSTRATE_KNOWLEDGE:
        substrate_info = SUBSTRATE_KNOWLEDGE[substrate]

        # Check if moisture interpretation needs adjustment
        moisture_status = plant_data.get("moisture_status", 2)

        if substrate == "lechuza_pon" and moisture_status == 1:
            recommendations.append({
                "type": "info",
                "category": "substrate_context",
                "priority": "medium",
                "message": "Lechuza-PON often shows 'low' at surface while reservoir is full. Check water indicator!",
                "explanation": substrate_info["recommendations"]["monitoring"]
            })

        if substrate == "mineral" and moisture_status == 1:
            recommendations.append({
                "type": "warning",
                "category": "substrate_context",
                "priority": "high",
                "message": "Mineral substrates dry quickly! Water more frequently than organic soil.",
                "explanation": substrate_info["recommendations"]["watering"]
            })

        # Fertilizer recommendations based on substrate
        if substrate in ["mineral", "semi_hydro", "hydroponic"]:
            recommendations.append({
                "type": "info",
                "category": "fertilizing",
                "priority": "low",
                "message": f"{substrate_info['description']} needs frequent fertilizing.",
                "explanation": substrate_info["recommendations"]["fertilizing"]
            })

    # Container-specific recommendations
    if container and container in CONTAINER_KNOWLEDGE:
        container_info = CONTAINER_KNOWLEDGE[container]

        if container == "lechuza":
            recommendations.append({
                "type": "info",
                "category": "container_context",
                "priority": "medium",
                "message": "Lechuza self-watering: Fill reservoir, don't top-water!",
                "explanation": container_info["recommendations"]["watering"]
            })

        if container == "terracotta":
            moisture_status = plant_data.get("moisture_status", 2)
            if moisture_status == 1:
                recommendations.append({
                    "type": "info",
                    "category": "container_context",
                    "priority": "medium",
                    "message": "Terracotta dries faster than plastic. This is normal for clay pots.",
                    "explanation": container_info["recommendations"]["watering"]
                })

    # Growth phase recommendations
    if growth_phase and growth_phase in GROWTH_PHASE_KNOWLEDGE:
        phase_info = GROWTH_PHASE_KNOWLEDGE[growth_phase]

        if growth_phase == "flowering":
            light_status = plant_data.get("light_status", 2)
            if light_status == 1:
                recommendations.append({
                    "type": "warning",
                    "category": "growth_phase",
                    "priority": "high",
                    "message": "Flowering phase needs HIGH light! Increase lighting ASAP.",
                    "explanation": phase_info["recommendations"]["lighting"]
                })

        if growth_phase == "dormant":
            moisture_status = plant_data.get("moisture_status", 2)
            if moisture_status == 3:
                recommendations.append({
                    "type": "warning",
                    "category": "growth_phase",
                    "priority": "medium",
                    "message": "Plant is dormant but soil is wet. Reduce watering to prevent root rot!",
                    "explanation": phase_info["recommendations"]["watering"]
                })

    return recommendations


def interpret_sensor_with_context(plant_data: Dict, context: Optional[Dict]) -> Dict:
    """
    Reinterpret sensor readings based on context

    Args:
        plant_data: Sensor data
        context: Plant context

    Returns:
        Adjusted interpretation
    """
    if not context:
        return {"adjusted": False, "note": "No context available"}

    adjustments = []

    substrate = context.get("substrate")
    container = context.get("container")

    # Lechuza-PON specific: "Low" moisture at top is often OK
    if substrate == "lechuza_pon" and plant_data.get("moisture_status") == 1:
        adjustments.append({
            "sensor": "moisture",
            "raw_status": "Low",
            "adjusted_status": "Normal for PON",
            "explanation": "Lechuza-PON stays dry at surface while wicking water from reservoir. Check reservoir level instead."
        })

    # Mineral substrate: Lower moisture is acceptable
    if substrate == "mineral" and plant_data.get("moisture_status") == 2:
        adjustments.append({
            "sensor": "moisture",
            "note": "Mineral substrates naturally read lower than organic soil. This 'optimal' reading is excellent!"
        })

    # Hydroponic: Sensors may not work correctly
    if substrate == "hydroponic":
        adjustments.append({
            "warning": "FYTA sensors not designed for hydroponic systems. Use EC/pH meters instead.",
            "ignore_sensors": ["moisture", "nutrients"]
        })

    return {
        "adjusted": len(adjustments) > 0,
        "adjustments": adjustments
    }
