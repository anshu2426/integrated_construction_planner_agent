"""
Deterministic Resource Tools for Construction Planning
Rule-based cost and duration calculations with permit and booking requirements
"""
from typing import Dict, Any
from datetime import datetime


# Cost configuration (INR - Indian Rupees)
COST_PER_SQFT = {
    "Basic": 1500,
    "Standard": 2200,
    "Premium": 3200
}

LOCATION_MULTIPLIER = {
    "Metro": 1.3,
    "Tier 2": 1.0,
    "Rural": 0.8
}

# Cost breakdown percentages
LABOR_PERCENTAGE = 0.4
MATERIAL_PERCENTAGE = 0.5
EQUIPMENT_PERCENTAGE = 0.1

# Permit and License Requirements Database
PERMIT_REQUIREMENTS = {
    "building_permit": {
        "required_for": ["all_projects"],
        "processing_time_days": "15-30",
        "submit_before_days": 30,
        "authority": "Local Municipal Corporation",
        "documents": ["site plan", "building plan", "structural certificate", "owner ID proof", "property documents"],
        "fees": "0.5% of construction cost",
        "validity": "5 years"
    },
    "excavation_permit": {
        "required_for": ["foundation", "site_preparation", "basement"],
        "processing_time_days": "7-14",
        "submit_before_days": 14,
        "authority": "Local Municipal Corporation",
        "documents": ["excavation plan", "safety plan", "neighbor consent (if applicable)", "insurance certificate"],
        "fees": "₹5,000 - ₹15,000",
        "validity": "6 months"
    },
    "electrical_permit": {
        "required_for": ["utilities", "new_construction", "renovation"],
        "processing_time_days": "7-10",
        "submit_before_days": 10,
        "authority": "State Electricity Board",
        "documents": ["electrical load calculation", "wiring diagram", "contractor license", "test certificate"],
        "fees": "₹2,000 - ₹10,000",
        "validity": "Until completion"
    },
    "water_connection": {
        "required_for": ["utilities", "new_construction"],
        "processing_time_days": "14-21",
        "submit_before_days": 21,
        "authority": "Local Water Authority / Municipal Corporation",
        "documents": ["water requirement calculation", "property documents", "ID proof", "NO objection from neighbors"],
        "fees": "₹10,000 - ₹25,000",
        "validity": "Permanent"
    },
    "fire_safety": {
        "required_for": ["commercial", "high_rise", "public_building"],
        "processing_time_days": "21-30",
        "submit_before_days": 30,
        "authority": "Fire Department",
        "documents": ["fire safety plan", "evacuation plan", "equipment list", "NO objection from fire department"],
        "fees": "₹15,000 - ₹50,000",
        "validity": "Until inspection"
    },
    "environmental_clearance": {
        "required_for": ["large_projects", "industrial", "commercial"],
        "processing_time_days": "30-45",
        "submit_before_days": 45,
        "authority": "State Pollution Control Board",
        "documents": ["environmental impact assessment", "waste management plan", "tree preservation plan"],
        "fees": "₹25,000 - ₹1,00,000",
        "validity": "Project duration"
    }
}

# Resource Booking Requirements Database
RESOURCE_BOOKING_REQUIREMENTS = {
    "labor": {
        "foundation": {
            "contact_before_days": 14,
            "book_through": "licensed_concrete_contractors",
            "typical_lead_time": "7-14 days",
            "deposit": "₹50,000 - ₹1,00,000",
            "notes": "Foundation specialists in high demand, book early. Verify contractor license and insurance.",
            "skills_required": ["concrete specialist", "foundation engineer", "site supervisor"]
        },
        "structural": {
            "contact_before_days": 21,
            "book_through": "structural_engineering_firms",
            "typical_lead_time": "14-21 days",
            "deposit": "₹1,00,000 - ₹2,00,000",
            "notes": "Structural engineers and steelworkers need advance booking. Ensure structural drawings are approved.",
            "skills_required": ["structural engineer", "certified welder", "crane operator", "rigging specialist"]
        },
        "utilities": {
            "contact_before_days": 10,
            "book_through": "licensed_utility_contractors",
            "typical_lead_time": "7-10 days",
            "deposit": "₹25,000 - ₹50,000",
            "notes": "Licensed electricians and plumbers require scheduling. Verify licenses for electrical and plumbing work.",
            "skills_required": ["licensed electrician", "licensed plumber", "HVAC technician"]
        },
        "finishing": {
            "contact_before_days": 7,
            "book_through": "general_contractors",
            "typical_lead_time": "5-7 days",
            "deposit": "₹25,000 - ₹50,000",
            "notes": "Finishing crew generally available but book during peak season (Oct-Mar) for better rates.",
            "skills_required": ["carpenter", "painter", "flooring specialist", "interior designer"]
        },
        "site_preparation": {
            "contact_before_days": 7,
            "book_through": "excavation_contractors",
            "typical_lead_time": "5-7 days",
            "deposit": "₹30,000 - ₹75,000",
            "notes": "Heavy equipment operators readily available. Check soil report before booking.",
            "skills_required": ["excavator operator", "heavy equipment operator", "site supervisor"]
        }
    },
    "materials": {
        "concrete": {
            "order_before_days": 5,
            "supplier_type": "ready_mix_concrete_companies",
            "typical_lead_time": "2-5 days",
            "minimum_order": "5 cubic meters",
            "notes": "Order 48 hours before pour for best scheduling. Consider weather conditions.",
            "suppliers": ["ACC Concrete", "UltraTech ReadyMix", "Local RMC plants"]
        },
        "steel": {
            "order_before_days": 14,
            "supplier_type": "steel_suppliers",
            "typical_lead_time": "10-14 days",
            "minimum_order": "1 ton",
            "notes": "Custom fabrication may require 3-4 weeks. Verify steel grade specifications.",
            "suppliers": ["Tata Steel", "JSW Steel", "Local steel merchants"]
        },
        "electrical_components": {
            "order_before_days": 7,
            "supplier_type": "electrical_wholesalers",
            "typical_lead_time": "5-7 days",
            "notes": "Specialty items (switchgear, panels) may require 2-3 weeks. Verify brand specifications.",
            "suppliers": ["Schneider Electric", "ABB", "Local electrical suppliers"]
        },
        "plumbing_materials": {
            "order_before_days": 5,
            "supplier_type": "plumbing_suppliers",
            "typical_lead_time": "3-5 days",
            "notes": "Standard items readily available. Custom fixtures may require 2-3 weeks.",
            "suppliers": ["Jaquar", "Kohler", "Local plumbing suppliers"]
        },
        "finishing_materials": {
            "order_before_days": 7,
            "supplier_type": "building_material_suppliers",
            "typical_lead_time": "5-7 days",
            "notes": "Natural stone, custom tiles may require 2-4 weeks. Check stock availability.",
            "suppliers": ["Asian Paints", "Kajaria Ceramics", "Local building material suppliers"]
        }
    },
    "equipment": {
        "crane": {
            "book_before_days": 7,
            "rental_type": "heavy_equipment_rental_agencies",
            "typical_lead_time": "5-7 days",
            "daily_rate": "₹15,000 - ₹25,000",
            "notes": "Cranes in high demand, book 1-2 weeks in advance. Requires certified operator.",
            "suppliers": ["Sany India", "JCB", "Local equipment rental"]
        },
        "excavator": {
            "book_before_days": 5,
            "rental_type": "heavy_equipment_rental_agencies",
            "typical_lead_time": "3-5 days",
            "daily_rate": "₹8,000 - ₹12,000",
            "notes": "Book during off-season (Apr-Sep) for better rates. Verify equipment condition.",
            "suppliers": ["JCB", "Caterpillar", "Local equipment rental"]
        },
        "concrete_mixer": {
            "book_before_days": 3,
            "rental_type": "equipment_rental",
            "typical_lead_time": "2-3 days",
            "daily_rate": "₹2,000 - ₹3,000",
            "notes": "Readily available, short notice acceptable. Consider ready-mix instead.",
            "suppliers": ["Local equipment rental", "Construction equipment suppliers"]
        },
        "scaffolding": {
            "book_before_days": 5,
            "rental_type": "scaffolding_suppliers",
            "typical_lead_time": "3-5 days",
            "daily_rate": "₹50 - ₹100 per sq ft",
            "notes": "Calculate height and area requirements. Safety inspection required.",
            "suppliers": ["Scaffolding India", "Local scaffolding suppliers"]
        }
    }
}

# Task to Permit Mapping
TASK_PERMIT_MAPPING = {
    "permits": ["building_permit"],
    "site_preparation": ["excavation_permit"],
    "foundation": ["building_permit", "excavation_permit"],
    "structural": ["building_permit"],
    "utilities": ["electrical_permit", "water_connection"],
    "finishing": ["building_permit"]
}


def calculate_project_cost(area: int, quality: str, location: str, floors: int = 1) -> Dict[str, Any]:
    """Calculate deterministic project cost based on parameters with floor scaling"""
    
    # Step 1: Add effective floor scaling (slight realism)
    effective_floors = 1 + 0.9 * (floors - 1)
    
    # Step 2: Calculate adjusted built-up area
    total_builtup_area = area * effective_floors
    
    # Step 3: Final cost calculation
    base_cost = total_builtup_area * COST_PER_SQFT[quality]
    final_cost = base_cost * LOCATION_MULTIPLIER[location]
    
    # Step 4: Cost breakdown
    labor_cost = final_cost * LABOR_PERCENTAGE
    material_cost = final_cost * MATERIAL_PERCENTAGE
    equipment_cost = final_cost * EQUIPMENT_PERCENTAGE
    
    return {
        "total_cost": int(final_cost),
        "labor_cost": int(labor_cost),
        "material_cost": int(material_cost),
        "equipment_cost": int(equipment_cost),
        "cost_per_sqft": COST_PER_SQFT[quality],
        "location_factor": LOCATION_MULTIPLIER[location],
        "currency": "INR",
        "effective_floors": round(effective_floors, 2),
        "total_builtup_area": int(total_builtup_area),
        "ground_floor_area": area
    }


def calculate_project_duration(area: int, floors: int, building_type: str = "Residential") -> Dict[str, Any]:
    """Calculate realistic project duration using phase-based construction modeling"""
    
    # Base duration for Indian construction scenarios
    base_duration_map = {
        "Residential": 120,  # 4 months for standard residential
        "Commercial": 180   # 6 months for standard commercial
    }
    
    # Step 2: Assign correct base duration
    selected_base_duration = base_duration_map[building_type]
    
    # Floor factor - each additional floor adds 30% time (diminishing returns)
    floor_factor = 1 + (floors - 1) * 0.3
    
    # Area factor - slight adjustment for area (not proportional)
    area_factor = 1 + ((area / 2000) - 1) * 0.2
    # Clamp to avoid extreme values
    area_factor = max(0.8, min(area_factor, 1.5))
    
    # Step 3: Calculate total duration
    total_duration = int(selected_base_duration * floor_factor * area_factor)
    
    # Phase breakdown using percentage distribution
    foundation_days = int(total_duration * 0.2)
    structure_days = int(total_duration * 0.5)
    finishing_days = total_duration - foundation_days - structure_days  # Ensure sum equals total
    
    return {
        "total_days": total_duration,
        "foundation_days": foundation_days,
        "structure_days": structure_days,
        "finishing_days": finishing_days,
        "base_duration": selected_base_duration,  # Fixed: was showing 0
        "floor_factor": round(floor_factor, 2),
        "area_factor": round(area_factor, 2),
        "building_type": building_type,
        "duration_per_sqft": total_duration / area if area > 0 else 0
    }


def check_labor_availability(task: Dict[str, Any]) -> Dict[str, Any]:
    """Return labor booking requirements instead of availability status"""
    task_category = task.get("category", "").lower()
    task_name = task.get("name", "").lower()
    
    # Get booking requirements for this category
    labor_requirements = RESOURCE_BOOKING_REQUIREMENTS.get("labor", {}).get(task_category, {})
    
    # Task-specific overrides based on keywords
    if "smart" in task_name or "automation" in task_name or "wiring" in task_name:
        labor_requirements = {
            "contact_before_days": 10,
            "book_through": "smart_home_installers",
            "typical_lead_time": "7-10 days",
            "deposit": "₹30,000 - ₹60,000",
            "notes": "Specialized installation requires certified technicians",
            "skills_required": ["electrician", "network technician", "home automation specialist"]
        }
    elif "kitchen" in task_name or "modular" in task_name:
        labor_requirements = {
            "contact_before_days": 14,
            "book_through": "modular_kitchen_installers",
            "typical_lead_time": "10-14 days",
            "deposit": "₹50,000 - ₹1,00,000",
            "notes": "Kitchen installation requires precise measurements",
            "skills_required": ["carpenter", "plumber", "electrician"]
        }
    elif "lighting" in task_name or "electrical" in task_name:
        labor_requirements = {
            "contact_before_days": 7,
            "book_through": "licensed_electricians",
            "typical_lead_time": "5-7 days",
            "deposit": "₹20,000 - ₹40,000",
            "notes": "Electrical work requires certified professionals",
            "skills_required": ["electrician", "lighting specialist"]
        }
    elif "insulation" in task_name or "drywall" in task_name:
        labor_requirements = {
            "contact_before_days": 7,
            "book_through": "insulation_contractors",
            "typical_lead_time": "5-7 days",
            "deposit": "₹20,000 - ₹40,000",
            "notes": "Insulation requires specialized equipment",
            "skills_required": ["insulation specialist", "drywall installer"]
        }
    elif "flooring" in task_name:
        labor_requirements = {
            "contact_before_days": 10,
            "book_through": "flooring_installers",
            "typical_lead_time": "7-10 days",
            "deposit": "₹30,000 - ₹60,000",
            "notes": "Flooring requires level surface preparation",
            "skills_required": ["flooring specialist", "tiler", "carpenter"]
        }
    
    # Default requirements if not found
    if not labor_requirements:
        labor_requirements = {
            "contact_before_days": 7,
            "book_through": "general_contractors",
            "typical_lead_time": "5-7 days",
            "deposit": "₹25,000 - ₹50,000",
            "notes": "Contact contractor in advance for scheduling",
            "skills_required": ["construction workers", "site supervisor"]
        }
    
    # Safe get with defaults
    contact_before = labor_requirements.get("contact_before_days", 7)
    book_through = labor_requirements.get("book_through", "general_contractors")
    lead_time = labor_requirements.get("typical_lead_time", "5-7 days")
    deposit = labor_requirements.get("deposit", "₹25,000 - ₹50,000")
    notes = labor_requirements.get("notes", "Contact contractor in advance")
    skills = labor_requirements.get("skills_required", ["construction workers"])
    
    return {
        "booking_required": True,
        "contact_before_days": contact_before,
        "book_through": book_through,
        "typical_lead_time": lead_time,
        "deposit": deposit,
        "notes": notes,
        "skills_required": skills,
        "check_date": datetime.now().strftime("%Y-%m-%d"),
        "task_name": task.get("name", "Unknown task")
    }


def check_material_availability(task: Dict[str, Any], project_cost: Dict[str, Any]) -> Dict[str, Any]:
    """Return material ordering requirements instead of availability status"""
    task_category = task.get("category", "").lower()
    task_name = task.get("name", "").lower()
    
    # Map task category to material type
    material_type_map = {
        "foundation": "concrete",
        "structural": "steel",
        "utilities": "electrical_components",
        "finishing": "finishing_materials",
        "site_preparation": "concrete"  # Gravel, sand
    }
    
    material_type = material_type_map.get(task_category, "finishing_materials")
    material_requirements = RESOURCE_BOOKING_REQUIREMENTS.get("materials", {}).get(material_type, {})
    
    # Task-specific overrides based on keywords
    if "smart" in task_name or "automation" in task_name or "wiring" in task_name:
        material_requirements = {
            "order_before_days": 10,
            "supplier_type": "smart_home_suppliers",
            "typical_lead_time": "7-10 days",
            "minimum_order": "Complete kit",
            "notes": "Smart home components require compatibility checks",
            "suppliers": ["Philips Hue", "Google Nest", "Amazon Alexa", "Local smart home dealers"]
        }
    elif "kitchen" in task_name or "modular" in task_name:
        material_requirements = {
            "order_before_days": 21,
            "supplier_type": "modular_kitchen_manufacturers",
            "typical_lead_time": "14-21 days",
            "minimum_order": "Full kitchen set",
            "notes": "Custom modular kitchens require design approval",
            "suppliers": ["Häfele", "Godrej Interio", "Urban Ladder", "Local kitchen manufacturers"]
        }
    elif "lighting" in task_name:
        material_requirements = {
            "order_before_days": 7,
            "supplier_type": "lighting_suppliers",
            "typical_lead_time": "5-7 days",
            "minimum_order": "Per fixture",
            "notes": "LED fixtures have different voltage requirements",
            "suppliers": ["Philips Lighting", "Osram", "Bajaj Electricals", "Local lighting stores"]
        }
    elif "insulation" in task_name or "drywall" in task_name:
        material_requirements = {
            "order_before_days": 7,
            "supplier_type": "insulation_suppliers",
            "typical_lead_time": "5-7 days",
            "minimum_order": "Per sq ft",
            "notes": "Insulation R-value affects thermal efficiency",
            "suppliers": ["Owens Corning", "Rockwool", "Local insulation suppliers"]
        }
    elif "flooring" in task_name:
        material_requirements = {
            "order_before_days": 10,
            "supplier_type": "flooring_suppliers",
            "typical_lead_time": "7-10 days",
            "minimum_order": "Per sq ft",
            "notes": "Flooring material depends on room usage",
            "suppliers": ["Kajaria Ceramics", "Johnson Tiles", "Asian Paints (flooring)", "Local tile dealers"]
        }
    
    # Default requirements if not found
    if not material_requirements:
        material_requirements = {
            "order_before_days": 7,
            "supplier_type": "building_material_suppliers",
            "typical_lead_time": "5-7 days",
            "minimum_order": "Standard quantity",
            "notes": "Order materials in advance for best scheduling",
            "suppliers": ["Local building material suppliers"]
        }
    
    # Safe get with defaults
    order_before = material_requirements.get("order_before_days", 7)
    supplier_type = material_requirements.get("supplier_type", "building_material_suppliers")
    lead_time = material_requirements.get("typical_lead_time", "5-7 days")
    min_order = material_requirements.get("minimum_order", "Standard quantity")
    notes = material_requirements.get("notes", "Order materials in advance")
    suppliers = material_requirements.get("suppliers", ["Local suppliers"])
    
    return {
        "ordering_required": True,
        "order_before_days": order_before,
        "supplier_type": supplier_type,
        "typical_lead_time": lead_time,
        "minimum_order": min_order,
        "notes": notes,
        "suppliers": suppliers,
        "check_date": datetime.now().strftime("%Y-%m-%d"),
        "task_name": task.get("name", "Unknown task")
    }


def check_equipment_availability(task: Dict[str, Any], project_cost: Dict[str, Any]) -> Dict[str, Any]:
    """Return equipment booking requirements instead of availability status"""
    task_category = task.get("category", "").lower()
    task_name = task.get("name", "").lower()
    
    # Map task category to equipment type
    equipment_type_map = {
        "foundation": "crane",
        "structural": "crane",
        "site_preparation": "excavator",
        "utilities": "concrete_mixer",
        "finishing": "scaffolding"
    }
    
    equipment_type = equipment_type_map.get(task_category, "concrete_mixer")
    equipment_requirements = RESOURCE_BOOKING_REQUIREMENTS.get("equipment", {}).get(equipment_type, {})
    
    # Task-specific overrides based on keywords
    if "smart" in task_name or "automation" in task_name or "wiring" in task_name:
        equipment_requirements = {
            "book_before_days": 7,
            "rental_type": "testing_equipment",
            "typical_lead_time": "3-5 days",
            "daily_rate": "₹5,000 - ₹8,000",
            "notes": "Smart home testing requires specialized tools",
            "suppliers": ["Fluke Corporation", "Klein Tools", "Local electrical equipment rental"]
        }
    elif "kitchen" in task_name or "modular" in task_name:
        equipment_requirements = {
            "book_before_days": 5,
            "rental_type": "installation_tools",
            "typical_lead_time": "3-5 days",
            "daily_rate": "₹3,000 - ₹5,000",
            "notes": "Kitchen installation requires precision tools",
            "suppliers": ["Bosch Power Tools", "Makita", "Local tool rental"]
        }
    elif "lighting" in task_name:
        equipment_requirements = {
            "book_before_days": 5,
            "rental_type": "electrical_testing_tools",
            "typical_lead_time": "2-3 days",
            "daily_rate": "₹2,000 - ₹4,000",
            "notes": "Lighting installation requires voltage testers",
            "suppliers": ["Megger", "Fluke", "Local electrical equipment rental"]
        }
    elif "insulation" in task_name or "drywall" in task_name:
        equipment_requirements = {
            "book_before_days": 5,
            "rental_type": "scaffolding",
            "typical_lead_time": "3-5 days",
            "daily_rate": "₹50 - ₹100 per sq ft",
            "notes": "Insulation work requires elevated access",
            "suppliers": ["Scaffolding India", "PERI", "Local scaffolding rental"]
        }
    elif "flooring" in task_name:
        equipment_requirements = {
            "book_before_days": 5,
            "rental_type": "flooring_tools",
            "typical_lead_time": "3-5 days",
            "daily_rate": "₹2,000 - ₹4,000",
            "notes": "Flooring requires tile cutters and levelers",
            "suppliers": ["Rubbermaid", "DEWALT", "Local tool rental"]
        }
    
    # Default requirements if not found
    if not equipment_requirements:
        equipment_requirements = {
            "book_before_days": 5,
            "rental_type": "equipment_rental",
            "typical_lead_time": "3-5 days",
            "daily_rate": "₹2,000 - ₹5,000",
            "notes": "Book equipment in advance for better rates",
            "suppliers": ["Local equipment rental"]
        }
    
    # Safe get with defaults
    book_before = equipment_requirements.get("book_before_days", 5)
    rental_type = equipment_requirements.get("rental_type", "equipment_rental")
    lead_time = equipment_requirements.get("typical_lead_time", "3-5 days")
    daily_rate = equipment_requirements.get("daily_rate", "₹2,000 - ₹5,000")
    notes = equipment_requirements.get("notes", "Book equipment in advance")
    suppliers = equipment_requirements.get("suppliers", ["Local equipment rental"])
    
    return {
        "booking_required": True,
        "book_before_days": book_before,
        "rental_type": rental_type,
        "typical_lead_time": lead_time,
        "daily_rate": daily_rate,
        "notes": notes,
        "suppliers": suppliers,
        "check_date": datetime.now().strftime("%Y-%m-%d"),
        "task_name": task.get("name", "Unknown task")
    }


def validate_all_resources(task: Dict[str, Any], project_cost: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive resource validation with permit and booking requirements"""
    labor = check_labor_availability(task)
    materials = check_material_availability(task, project_cost)
    equipment = check_equipment_availability(task, project_cost)
    
    # Get permits for this task
    task_category = task.get("category", "").lower()
    task_name = task.get("name", "").lower()
    permit_types = TASK_PERMIT_MAPPING.get(task_category, [])
    
    # Task-specific permit overrides
    if "smart" in task_name or "automation" in task_name or "wiring" in task_name:
        permit_types = ["electrical_permit"]
    elif "kitchen" in task_name or "modular" in task_name:
        permit_types = ["building_permit", "plumbing_permit"]
    elif "lighting" in task_name:
        permit_types = ["electrical_permit"]
    elif "final" in task_name or "inspection" in task_name:
        permit_types = ["completion_certificate"]
    
    permits_required = []
    for permit_type in permit_types:
        permit_info = PERMIT_REQUIREMENTS.get(permit_type, {})
        if permit_info:
            permits_required.append(permit_info)
    
    # Calculate costs based on category allocation
    total_labor_cost = project_cost["labor_cost"]
    total_material_cost = project_cost["material_cost"]
    total_equipment_cost = project_cost["equipment_cost"]
    
    category_labor_allocation = {
        "permits": 0.05,
        "site_preparation": 0.15,
        "foundation": 0.20,
        "structural": 0.30,
        "utilities": 0.20,
        "finishing": 0.10
    }
    
    category_material_allocation = {
        "permits": 0.02,
        "site_preparation": 0.05,
        "foundation": 0.25,
        "structural": 0.30,
        "utilities": 0.20,
        "finishing": 0.18
    }
    
    category_equipment_allocation = {
        "permits": 0.05,
        "site_preparation": 0.25,
        "foundation": 0.20,
        "structural": 0.30,
        "utilities": 0.10,
        "finishing": 0.10
    }
    
    labor_allocation = category_labor_allocation.get(task_category, 0.1)
    material_allocation = category_material_allocation.get(task_category, 0.1)
    equipment_allocation = category_equipment_allocation.get(task_category, 0.1)
    
    task_labor_cost = int(total_labor_cost * labor_allocation)
    task_material_cost = int(total_material_cost * material_allocation)
    task_equipment_cost = int(total_equipment_cost * equipment_allocation)
    
    total_cost = task_labor_cost + task_material_cost + task_equipment_cost
    
    return {
        "task_id": task.get("id", ""),
        "task_name": task.get("name", ""),
        "validation_status": "ready_for_planning",
        "overall_available": True,  # Planning tool - requirements are identified, resources can be booked
        "labor_available": True,
        "material_available": True,
        "equipment_available": True,
        "labor": labor,
        "materials": materials,
        "equipment": equipment,
        "permits_required": permits_required,
        "total_estimated_cost": f"₹{total_cost:,}",
        "labor_cost": f"₹{task_labor_cost:,}",
        "material_cost": f"₹{task_material_cost:,}",
        "equipment_cost": f"₹{task_equipment_cost:,}",
        "validation_notes": "All booking and permit requirements identified",
        "validation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
