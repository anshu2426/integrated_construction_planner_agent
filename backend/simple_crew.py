"""
Hybrid Construction Planning: Deterministic Costs + LLM Task Planning
Rule-based cost and duration calculations with LLM for task breakdown only
Enhanced with AI-powered feature extraction and intelligent insights
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from typing import Dict, Any
from tools.resource_tools import (
    calculate_project_cost,
    calculate_project_duration
)
from feature_extractor import extract_features
from ai_planner import AIPlanner
from agents.planner import PlannerAgent
from agents.validator import ResourceValidatorAgent
from agents.scheduler import SchedulerAgent


class SimpleConstructionPlanner:
    """Hybrid construction planning with deterministic costs and LLM task planning"""
    
    def __init__(self):
        self.ai_planner = AIPlanner()
        # Initialize CrewAI agents for enhanced capabilities
        self.planner_agent = PlannerAgent()
        self.validator_agent = ResourceValidatorAgent()
        self.scheduler_agent = SchedulerAgent()
    
    def plan_construction_project(self, project_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete construction planning workflow with AI enhancement"""
        try:
            # Extract project parameters
            area = project_params.get("area", 2000)
            floors = project_params.get("floors", 2)
            building_type = project_params.get("building_type", "Residential")
            quality = project_params.get("quality", "Standard")
            location = project_params.get("location", "Tier 2")
            description = project_params.get("description", f"{building_type} building")
            
            # Step 1: Extract features from description
            features = extract_features(description)
            
            # Step 2: Calculate base deterministic costs and duration
            base_cost_analysis = calculate_project_cost(area, quality, location, floors)
            base_duration_analysis = calculate_project_duration(area, floors, building_type)
            
            # Step 3: Apply feature-based adjustments
            enhanced_cost_analysis = self._apply_feature_adjustments(base_cost_analysis, features)
            enhanced_duration_analysis = self._apply_duration_adjustments(base_duration_analysis, features)
            
            # Step 4: Generate AI insights
            ai_insights = self.ai_planner.generate_ai_insights(project_params)
            
            # Step 5: Generate task breakdown using Planner Agent (with enhanced parameters)
            tasks = self.planner_agent.create_task_breakdown(description, enhanced_duration_analysis, features)
            
            if not tasks or not tasks.get("tasks"):
                error_msg = f"Failed to generate tasks. Response: {tasks}"
                import logging
                logging.error(error_msg)
                return self._create_error_response("planning", "Failed to generate tasks", description)
            
            # Step 6: Add feature-based extra tasks
            enhanced_tasks = self._add_feature_tasks(tasks, features)
            
            # Step 7: Resource Validation using Validator Agent with enhanced costs
            validation_results = self.validator_agent.validate_tasks(enhanced_tasks.get("tasks", []), enhanced_cost_analysis)
            
            # Step 8: Create schedule using Scheduler Agent based on enhanced duration
            schedule_results = self.scheduler_agent.create_schedule(
                validation_results.get("validated_tasks", []), 
                enhanced_duration_analysis
            )
            
            # Step 9: Merge AI insights with rule-based results
            merged_results = self.ai_planner.merge_with_rule_based(
                ai_insights, 
                enhanced_tasks.get("tasks", []),
                enhanced_duration_analysis["total_days"],
                enhanced_cost_analysis
            )
            
            # Step 10: Compile final results
            final_result = self._compile_final_results(
                project_params, enhanced_cost_analysis, enhanced_duration_analysis, 
                enhanced_tasks, validation_results, schedule_results, features, ai_insights, merged_results
            )
            
            return final_result
            
        except Exception as e:
            return self._create_error_response("workflow", str(e), str(project_params))
    
    def _apply_feature_adjustments(self, base_cost_analysis: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """Apply feature-based cost adjustments"""
        enhanced_cost = base_cost_analysis.copy()
        
        if features.get("has_features", False):
            cost_multiplier = features.get("cost_multiplier", 1.0)
            
            # Apply cost multiplier
            enhanced_cost["total_cost"] = int(base_cost_analysis["total_cost"] * cost_multiplier)
            enhanced_cost["labor_cost"] = int(base_cost_analysis["labor_cost"] * cost_multiplier)
            enhanced_cost["material_cost"] = int(base_cost_analysis["material_cost"] * cost_multiplier)
            enhanced_cost["equipment_cost"] = int(base_cost_analysis["equipment_cost"] * cost_multiplier)
            
            # Add feature metadata
            enhanced_cost["base_cost"] = base_cost_analysis["total_cost"]
            enhanced_cost["feature_multiplier"] = cost_multiplier
            enhanced_cost["cost_increase"] = enhanced_cost["total_cost"] - base_cost_analysis["total_cost"]
        
        return enhanced_cost
    
    def _apply_duration_adjustments(self, base_duration_analysis: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """Apply feature-based duration adjustments"""
        enhanced_duration = base_duration_analysis.copy()
        
        if features.get("has_features", False):
            extra_days = features.get("extra_days", 0)
            
            # Apply extra days
            enhanced_duration["total_days"] = base_duration_analysis["total_days"] + extra_days
            
            # Redistribute phases proportionally
            if extra_days != 0:
                total_original = base_duration_analysis["total_days"]
                foundation_extra = int(extra_days * 0.2)
                structure_extra = int(extra_days * 0.5)
                finishing_extra = extra_days - foundation_extra - structure_extra
                
                enhanced_duration["foundation_days"] = base_duration_analysis["foundation_days"] + foundation_extra
                enhanced_duration["structure_days"] = base_duration_analysis["structure_days"] + structure_extra
                enhanced_duration["finishing_days"] = base_duration_analysis["finishing_days"] + finishing_extra
            
            # Add feature metadata
            enhanced_duration["base_duration"] = base_duration_analysis["total_days"]
            enhanced_duration["extra_days"] = extra_days
            enhanced_duration["duration_increase"] = extra_days
        
        return enhanced_duration
    
    def _add_feature_tasks(self, tasks: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """Add feature-based extra tasks to the task list"""
        enhanced_tasks = tasks.copy()
        
        if features.get("has_features", False):
            extra_tasks = features.get("extra_tasks", [])
            existing_tasks = tasks.get("tasks", [])
            
            # Add extra tasks with special markers
            for i, task_description in enumerate(extra_tasks):
                extra_task = {
                    "id": f"feature_task_{i+1}",
                    "name": task_description,
                    "description": f"Additional task based on project features: {task_description}",
                    "category": "special",
                    "estimated_duration_days": 5,  # Default duration for feature tasks
                    "dependencies": [],
                    "feature_generated": True
                }
                existing_tasks.append(extra_task)
            
            enhanced_tasks["tasks"] = existing_tasks
        
        return enhanced_tasks
    
    def _compile_final_results(self, project_params: Dict[str, Any], cost_analysis: Dict[str, Any], 
                             duration_analysis: Dict[str, Any], tasks: dict, validation: dict, 
                             schedule: dict, features: Dict[str, Any], ai_insights: Dict[str, Any], 
                             merged_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile final results with AI enhancement and feature extraction"""
        total_tasks = len(tasks.get("tasks", []))
        validated_tasks_list = validation.get("validated_tasks", [])
        approved_tasks = sum(1 for t in validated_tasks_list if t.get("overall_available", False))
        total_duration = duration_analysis["total_days"]
        total_cost = cost_analysis["total_cost"]
        
        # Calculate enhanced health metrics
        health_metrics = self._calculate_enhanced_health_metrics(
            validated_tasks_list, total_tasks, schedule, cost_analysis, duration_analysis
        )
        
        return {
            "project_metadata": {
                "goal": project_params.get("description", ""),
                "area": project_params.get("area"),
                "floors": project_params.get("floors"),
                "building_type": project_params.get("building_type"),
                "quality": project_params.get("quality"),
                "location": project_params.get("location"),
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_tasks": total_tasks,
                "total_duration_days": total_duration,
                "total_estimated_cost": f"₹{total_cost:,}"
            },
            "cost_breakdown": {
                "total_cost": f"₹{total_cost:,}",
                "labor_cost": f"₹{cost_analysis['labor_cost']:,}",
                "material_cost": f"₹{cost_analysis['material_cost']:,}",
                "equipment_cost": f"₹{cost_analysis['equipment_cost']:,}",
                "cost_per_sqft": f"₹{cost_analysis['cost_per_sqft']:,}",
                "location_factor": cost_analysis['location_factor'],
                "ground_floor_area": project_params.get("area"),
                "effective_floors": cost_analysis.get('effective_floors', 1.0),
                "total_builtup_area": cost_analysis.get('total_builtup_area', project_params.get("area", 0)),
                # Feature-based cost information
                "base_cost": f"₹{cost_analysis.get('base_cost', total_cost):,}",
                "feature_multiplier": cost_analysis.get('feature_multiplier', 1.0),
                "cost_increase": f"₹{cost_analysis.get('cost_increase', 0):,}",
                "ai_optimization_tips": merged_results.get("merged_cost", {}).get("ai_optimization_tips", []),
                "potential_cost_savers": merged_results.get("merged_cost", {}).get("potential_cost_savers", [])
            },
            "duration_breakdown": {
                "total_days": total_duration,
                "foundation_days": duration_analysis["foundation_days"],
                "structure_days": duration_analysis["structure_days"],
                "finishing_days": duration_analysis["finishing_days"],
                "base_duration": duration_analysis.get("base_duration", 0),
                "floor_factor": duration_analysis.get("floor_factor", 1.0),
                "area_factor": duration_analysis.get("area_factor", 1.0),
                "days_per_sqft": round(duration_analysis["duration_per_sqft"], 3),
                # Feature-based duration information
                "extra_days": duration_analysis.get("extra_days", 0),
                "duration_increase": duration_analysis.get("duration_increase", 0),
                "duration_insights": merged_results.get("duration_insights", {})
            },
            "task_breakdown": tasks,
            "resource_validation": validation,
            "project_schedule": schedule,
            "project_health": health_metrics,
            "summary": {
                "project_overview": f"Construction plan for '{project_params.get('description', '')}' - {project_params.get('area')} sq ft, {project_params.get('floors')} floors",
                "key_highlights": [
                    f"{approved_tasks} of {total_tasks} tasks approved for execution",
                    f"Estimated project duration: {total_duration} days",
                    f"Total estimated cost: ₹{total_cost:,}",
                    f"Cost per sq ft: ₹{cost_analysis['cost_per_sqft']:,}"
                ]
            },
            # NEW: AI Enhancement sections
            "feature_extraction": {
                "features_detected": features.get("features_detected", []),
                "has_features": features.get("has_features", False),
                "cost_multiplier": features.get("cost_multiplier", 1.0),
                "extra_days": features.get("extra_days", 0),
                "extra_tasks_count": len(features.get("extra_tasks", [])),
                "feature_summary": self._generate_feature_summary(features)
            },
            "ai_insights": {
                "status": ai_insights.get("status", "error"),
                "ai_enhancement": merged_results.get("ai_enhancement", False),
                "ai_analysis": merged_results.get("ai_analysis", {}),
                "ai_recommendations": merged_results.get("ai_recommendations", []),
                "enhanced_tasks": [task for task in merged_results.get("merged_tasks", []) if task.get("ai_generated")],
                "enhanced_tasks_count": len([task for task in merged_results.get("merged_tasks", []) if task.get("ai_generated")])
            },
            "estimation_methodology": "Hybrid AI-enhanced deterministic calculations with feature extraction",
            "status": "completed"
        }
    
    def _calculate_enhanced_health_metrics(self, validated_tasks: list, total_tasks: int, 
                                         schedule: dict, cost_analysis: dict, 
                                         duration_analysis: dict) -> Dict[str, Any]:
        """Calculate enhanced health metrics with practical dimensions"""
        if not validated_tasks:
            return self._get_default_health_metrics()
        
        # Extract project parameters for dynamic scoring
        area = cost_analysis.get("total_builtup_area", 2000)
        location = cost_analysis.get("location_factor", 1.0)
        floors = cost_analysis.get("effective_floors", 1)
        total_duration = duration_analysis.get("total_days", 120)
        
        # 1. Resource Health (based on project complexity and location)
        # Larger projects in metros have harder resource availability
        base_resource_health = 100.0
        complexity_penalty = 0
        
        # Area penalty: larger projects = harder to coordinate resources
        if area > 5000:
            complexity_penalty += 15
        elif area > 3000:
            complexity_penalty += 10
        elif area > 2000:
            complexity_penalty += 5
        
        # Location penalty: metros have more competition for resources
        if location >= 1.3:  # Metro
            complexity_penalty += 10
        elif location >= 1.0:  # Tier 2
            complexity_penalty += 5
        
        # Floor penalty: multi-story requires specialized resources
        if floors > 3:
            complexity_penalty += 10
        elif floors > 1:
            complexity_penalty += 5
        
        resource_health = max(60, base_resource_health - complexity_penalty)
        
        # 2. Schedule Confidence (refined based on project complexity)
        base_confidence = schedule.get("schedule_confidence", 8)
        
        # Reduce confidence for complex projects
        if total_duration > 180:  # 6+ months
            base_confidence = max(5, base_confidence - 2)
        elif total_duration > 120:  # 4+ months
            base_confidence = max(6, base_confidence - 1)
        
        schedule_confidence = base_confidence
        
        # 3. Critical Path Health (based on resource constraints)
        critical_path_tasks = schedule.get("critical_path_tasks", [])
        if critical_path_tasks:
            # Critical path harder in complex projects
            critical_path_health = resource_health - 5  # Slightly lower than overall
            critical_path_health = max(50, critical_path_health)
        else:
            critical_path_health = resource_health
        
        # 4. Timeline Buffer Health (check if buffer is adequate for project complexity)
        buffer_days = schedule.get("buffer_days", 0)
        buffer_percentage = round((buffer_days / total_duration * 100) if total_duration > 0 else 0, 1)
        
        # Complex projects need more buffer
        required_buffer = 10
        if floors > 2:
            required_buffer = 15
        if area > 3000:
            required_buffer = 15
        if location >= 1.3:  # Metro
            required_buffer = 15
        
        if buffer_percentage >= required_buffer:
            timeline_health = min(100, buffer_percentage * 2)
        else:
            timeline_health = max(30, buffer_percentage * 4)
        
        # 5. Permit Compliance Health (varies by building type and location)
        permit_compliant = 0
        tasks_with_permits = 0
        tight_permit_count = 0
        
        for task in validated_tasks:
            permits = task.get("permits_required", [])
            if permits:
                tasks_with_permits += 1
                # Check if any permit has adequate lead time
                if any(p.get("submit_before_days", 0) >= 7 for p in permits):
                    permit_compliant += 1
                else:
                    tight_permit_count += 1
        
        base_permit_health = round((permit_compliant / tasks_with_permits * 100) if tasks_with_permits > 0 else 100, 1)
        
        # Reduce permit health for metros (stricter regulations, slower processing)
        if location >= 1.3 and tight_permit_count > 0:
            base_permit_health = max(60, base_permit_health - 15)
        elif location >= 1.0 and tight_permit_count > 0:
            base_permit_health = max(70, base_permit_health - 10)
        
        permit_health = base_permit_health
        
        # 6. Overall Health Score (weighted average)
        weights = {
            "resource": 0.35,
            "schedule": 0.25,
            "critical_path": 0.20,
            "timeline": 0.10,
            "permit": 0.10
        }
        overall_health = round(
            resource_health * weights["resource"] +
            (schedule_confidence * 10) * weights["schedule"] +
            critical_path_health * weights["critical_path"] +
            timeline_health * weights["timeline"] +
            permit_health * weights["permit"]
        , 1)
        
        # 7. Risk Level (5-level based on overall health and critical factors)
        risk_level = self._calculate_risk_level(overall_health, critical_path_health, resource_health)
        
        # 8. Actionable Recommendations
        recommendations = self._generate_health_recommendations(
            resource_health, critical_path_health, timeline_health, permit_health, 
            validated_tasks, area, location, floors
        )
        
        # 9. Risk Factors based on project characteristics
        risk_factors = self._identify_dynamic_risk_factors(
            validated_tasks, critical_path_tasks, area, location, floors, total_duration
        )
        
        return {
            "overall_health_score": overall_health,
            "resource_health": resource_health,
            "schedule_confidence": schedule_confidence,
            "critical_path_health": critical_path_health,
            "timeline_buffer_health": timeline_health,
            "permit_compliance_health": permit_health,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "metrics_summary": {
                "total_tasks": total_tasks,
                "approved_tasks": total_tasks,  # All tasks have requirements identified
                "critical_tasks": len(critical_path_tasks),
                "buffer_days": buffer_days,
                "buffer_percentage": buffer_percentage,
                "complexity_factors": {
                    "area": area,
                    "location_factor": location,
                    "floors": floors,
                    "duration_days": total_duration
                }
            }
        }
    
    def _calculate_risk_level(self, overall_health: float, critical_path_health: float, 
                             resource_health: float) -> str:
        """Calculate 5-level risk assessment based on key factors"""
        # Critical path health is most important
        if critical_path_health < 50:
            return "Critical"
        elif critical_path_health < 70 or overall_health < 50:
            return "High"
        elif overall_health < 70 or resource_health < 70:
            return "Medium"
        elif overall_health < 85:
            return "Low"
        else:
            return "Very Low"
    
    def _identify_health_risk_factors(self, validated_tasks: list, critical_path_tasks: list) -> list:
        """Identify specific risk factors based on task validation"""
        risk_factors = []
        
        for task in validated_tasks:
            task_id = task.get("task_id", "")
            
            # Check resource constraints
            if not task.get("overall_available"):
                risk_factors.append(f"Resource constraint: {task.get('task_name', 'Unknown task')}")
            
            # Check critical path issues
            if task_id in critical_path_tasks and not task.get("overall_available"):
                risk_factors.append(f"Critical path risk: {task.get('task_name', 'Unknown task')}")
            
            # Check permit lead time issues
            permits = task.get("permits_required", [])
            for permit in permits:
                if permit.get("submit_before_days", 0) < 7:
                    risk_factors.append(f"Tight permit timeline: {permit.get('authority', 'Unknown authority')}")
        
        return list(set(risk_factors))[:5]  # Limit to top 5 unique factors
    
    def _identify_dynamic_risk_factors(self, validated_tasks: list, critical_path_tasks: list, 
                                       area: float, location: float, floors: float, 
                                       total_duration: int) -> list:
        """Identify risk factors based on project characteristics"""
        risk_factors = []
        
        # Area-based risks
        if area > 5000:
            risk_factors.append("Large project coordination complexity")
        elif area > 3000:
            risk_factors.append("Medium-sized project requires careful resource management")
        
        # Location-based risks
        if location >= 1.3:  # Metro
            risk_factors.append("Metro area: Higher labor and material costs")
            risk_factors.append("Metro area: Stricter regulations and longer permit processing")
        elif location < 1.0:  # Rural
            risk_factors.append("Rural area: Limited supplier availability")
            risk_factors.append("Rural area: Potential transportation delays")
        
        # Floor-based risks
        if floors > 5:
            risk_factors.append("High-rise: Specialized equipment and safety requirements")
        elif floors > 3:
            risk_factors.append("Multi-story: Requires structural engineering expertise")
        elif floors > 1:
            risk_factors.append("Multi-story: Complex coordination between floors")
        
        # Duration-based risks
        if total_duration > 240:  # 8+ months
            risk_factors.append("Long project: Weather and seasonal impacts")
        elif total_duration > 180:  # 6+ months
            risk_factors.append("Extended timeline: Resource availability fluctuations")
        
        # Critical path risks
        if critical_path_tasks:
            critical_count = len(critical_path_tasks)
            if critical_count > 5:
                risk_factors.append(f"Many critical tasks ({critical_count}) - tight schedule")
        
        # Task-based risks
        for task in validated_tasks:
            permits = task.get("permits_required", [])
            if permits:
                for permit in permits:
                    if permit.get("submit_before_days", 0) < 14:
                        risk_factors.append(f"Tight permit timeline: {permit.get('authority', 'Authority')}")
        
        return list(set(risk_factors))[:6]  # Limit to top 6 unique factors
    
    def _generate_health_recommendations(self, resource_health: float, critical_path_health: float,
                                         timeline_health: float, permit_health: float,
                                         validated_tasks: list, area: float, location: float, 
                                         floors: float) -> list:
        """Generate actionable recommendations based on health metrics and project complexity"""
        recommendations = []
        
        # Resource-based recommendations
        if resource_health < 80:
            recommendations.append("Book resources early due to high demand in this area")
            if location >= 1.3:  # Metro
                recommendations.append("Consider premium suppliers for faster delivery in metro areas")
            if floors > 2:
                recommendations.append("Secure specialized contractors for multi-story construction")
        
        # Critical path recommendations
        if critical_path_health < 80:
            recommendations.append("Prioritize resource allocation for critical path tasks")
            recommendations.append("Consider fast-tracking critical path activities")
        
        # Timeline recommendations
        if timeline_health < 70:
            recommendations.append(f"Increase project buffer to at least {15 if floors > 2 or area > 3000 else 10}%")
            recommendations.append("Review schedule for parallelization opportunities")
        elif timeline_health < 85:
            recommendations.append("Monitor buffer utilization closely during execution")
        
        # Permit recommendations
        if permit_health < 80:
            recommendations.append("Initiate permit applications immediately - metro areas have longer processing")
            recommendations.append("Engage with permitting authorities early to understand requirements")
        
        # Location-specific recommendations
        if location >= 1.3:  # Metro
            recommendations.append("Plan for additional time in metro areas due to regulations")
        elif location < 1.0:  # Rural
            recommendations.append("Verify supplier availability in rural areas")
        
        # Size-specific recommendations
        if area > 3000:
            recommendations.append("Implement phased construction for large projects")
        if floors > 3:
            recommendations.append("Ensure specialized equipment for high-rise construction")
        
        if not recommendations:
            recommendations.append("Project health is good - continue regular monitoring")
        
        return recommendations[:6]  # Limit to top 6 recommendations
    
    def _get_default_health_metrics(self) -> Dict[str, Any]:
        """Return default health metrics when no tasks available"""
        return {
            "overall_health_score": 50.0,
            "resource_health": 50.0,
            "schedule_confidence": 5,
            "critical_path_health": 50.0,
            "timeline_buffer_health": 50.0,
            "permit_compliance_health": 100.0,
            "risk_level": "Medium",
            "risk_factors": ["No tasks to analyze"],
            "recommendations": ["Add tasks to enable health assessment"],
            "metrics_summary": {
                "total_tasks": 0,
                "approved_tasks": 0,
                "critical_tasks": 0,
                "buffer_days": 0,
                "buffer_percentage": 0
            }
        }
    
    def _generate_feature_summary(self, features: Dict[str, Any]) -> str:
        """Generate a human-readable feature summary"""
        if not features.get("has_features", False):
            return "No special features detected. Using standard construction planning."
        
        detected = features.get("features_detected", [])
        if not detected:
            return "No special features detected. Using standard construction planning."
        
        summary_parts = []
        for feature in detected:
            summary_parts.append(f"{feature['description']} ({feature['cost_impact']} cost, {feature['days_impact']} days)")
        
        return f"Detected features: " + ", ".join(summary_parts)
    
    def _create_error_response(self, error_type: str, error_message: str, project_info: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "project_metadata": {
                "goal": project_info,
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "error": {
                "type": error_type,
                "message": error_message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "status": "failed"
        }


# Update the app.py to use this improved version
def plan_construction_project(project_params: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function"""
    planner = SimpleConstructionPlanner()
    return planner.plan_construction_project(project_params)
