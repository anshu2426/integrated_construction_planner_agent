"""
Resource Validator Agent for Construction Planning Assistant
Validates labor, material, and equipment availability
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Agent
from config.llm_config import get_groq_llm_for_crewai, VALIDATOR_PROMPT, get_groq_llm
from tools.resource_tools import validate_all_resources
import json
import re


class ResourceValidatorAgent:
    """Resource Validation Expert Agent"""
    
    def __init__(self):
        self.llm = get_groq_llm_for_crewai()
        self.agent = Agent(
            role='Resource Validation Expert',
            goal='Validate construction tasks by checking labor, material, and equipment availability',
            backstory="""You are a resource management specialist with extensive experience in construction 
            logistics and supply chain management. You excel at identifying potential resource constraints, 
            validating material availability, checking labor capacity, and ensuring equipment availability. 
            You provide detailed feedback on resource feasibility and suggest alternatives when constraints exist.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            system_prompt=VALIDATOR_PROMPT
        )
    
    def validate_tasks(self, tasks: list, cost_analysis: dict) -> dict:
        """Validate and provide permit/booking requirements for all tasks"""
        validated_tasks = []
        
        for task in tasks:
            # Use the tools to get permit and booking requirements
            validation_result = validate_all_resources(task, cost_analysis)
            
            # Preserve LLM-generated duration
            validation_result['estimated_duration_days'] = task.get('estimated_duration_days', 0)
            
            # Use basic summary instead of LLM to avoid rate limits
            validation_result["requirement_summary"] = self._generate_basic_summary(validation_result)
            
            validated_tasks.append(validation_result)
        
        return {
            "validated_tasks": validated_tasks,
            "total_tasks": len(validated_tasks),
            "total_permits": sum(len(t.get('permits_required', [])) for t in validated_tasks)
        }
    
    def _enhance_validation_with_llm(self, validated_tasks: list, cost_analysis: dict) -> list:
        """Use LLM to generate concise summaries of requirements"""
        try:
            for task in validated_tasks:
                # Generate concise summary using LLM
                summary = self._generate_requirement_summary(task)
                task["requirement_summary"] = summary
            return validated_tasks
        except Exception as e:
            print(f"Error in LLM enhancement: {e}")
            # Fallback to basic summary if LLM fails
            for task in validated_tasks:
                task["requirement_summary"] = self._generate_basic_summary(task)
            return validated_tasks
    
    def _generate_requirement_summary(self, task: dict) -> str:
        """Use LLM to generate unique, contextual summary for each task"""
        try:
            # Extract key information
            task_name = task.get("task_name", "Task")
            permits = task.get("permits_required", [])
            labor = task.get("labor", {})
            materials = task.get("materials", {})
            equipment = task.get("equipment", {})
            
            # Build permit info
            permit_text = ""
            if permits:
                permit_text = f"Permits: "
                for i, permit in enumerate(permits):
                    permit_text += f"{permit.get('authority', 'Authority')} permit (submit {permit.get('submit_before_days', 'N/A')} days before, {permit.get('processing_time_days', 'N/A')} processing, fees: {permit.get('fees', 'N/A')})"
                    if i < len(permits) - 1:
                        permit_text += "; "
            
            # Build labor info
            labor_text = f"Labor: Contact {labor.get('book_through', 'contractors')} {labor.get('contact_before_days', 'N/A')} days before (lead time: {labor.get('typical_lead_time', 'N/A')}, deposit: {labor.get('deposit', 'N/A')}, skills: {', '.join(labor.get('skills_required', []))})"
            
            # Build material info
            material_text = f"Materials: Order from {materials.get('supplier_type', 'suppliers')} {materials.get('order_before_days', 'N/A')} days before (lead time: {materials.get('typical_lead_time', 'N/A')}, suppliers: {', '.join(materials.get('suppliers', []))})"
            
            # Build equipment info
            equipment_text = f"Equipment: Book {equipment.get('rental_type', 'equipment')} {equipment.get('book_before_days', 'N/A')} days before (rate: {equipment.get('daily_rate', 'N/A')}, suppliers: {', '.join(equipment.get('suppliers', []))})"
            
            prompt = f"""Write a natural, contextual 5-7 line summary for this construction task. Make it unique and specific to this task.

Task: {task_name}

Requirements to include:
{permit_text}
{labor_text}
{material_text}
{equipment_text}

Instructions:
- Write naturally, not as a list
- Make it specific to this task (e.g., "for smart home installation" vs generic)
- Vary the wording for each task
- Include all specific details (authorities, fees, suppliers, skills, rates)
- Make it actionable and clear
- 5-7 lines total
- DO NOT repeat the same format for every task"""

            llm = get_groq_llm()
            response = llm.invoke(prompt)
            
            # Clean up the response - handle AIMessage object
            summary = str(response.content).strip() if hasattr(response, 'content') else str(response).strip()
            if len(summary) > 600:
                summary = summary[:600] + "..."
            
            return summary
            
        except Exception as e:
            print(f"LLM call failed: {e}")
            return self._generate_basic_summary(task)
    
    def _generate_basic_summary(self, task: dict) -> str:
        """Generate a varied, contextual summary without LLM"""
        task_name = task.get("task_name", "Task")
        permits = task.get("permits_required", [])
        labor = task.get("labor", {})
        materials = task.get("materials", {})
        equipment = task.get("equipment", {})
        
        # Build permit details with variation
        if permits:
            permit_desc = f"Before starting {task_name.lower()}, you need to submit permits to "
            permit_desc += f"{permits[0].get('authority', 'authority')} {permits[0].get('submit_before_days', 'N/A')} days in advance"
            if len(permits) > 1:
                permit_desc += f" and {permits[1].get('authority', 'authority')} {permits[1].get('submit_before_days', 'N/A')} days before"
            permit_desc += f". Processing takes {permits[0].get('processing_time_days', 'N/A')} with fees of {permits[0].get('fees', 'N/A')}."
        else:
            permit_desc = ""
        
        # Build labor description with variation
        labor_desc = f"For {task_name.lower()}, contact {labor.get('book_through', 'contractors')} about {labor.get('contact_before_days', 'N/A')} days ahead of time. "
        labor_desc += f"Expect a {labor.get('typical_lead_time', 'N/A')} lead time and budget for a {labor.get('deposit', 'N/A')} deposit. "
        labor_desc += f"You'll need workers skilled in {', '.join(labor.get('skills_required', [])[:2])}."
        
        # Build material description with variation
        material_desc = f"Order materials from {materials.get('supplier_type', 'suppliers')} {materials.get('order_before_days', 'N/A')} days before {task_name.lower()}. "
        material_desc += f"Lead time is {materials.get('typical_lead_time', 'N/A')}. Consider suppliers like {materials.get('suppliers', [''])[0]} if available."
        
        # Build equipment description with variation
        equipment_desc = f"Reserve {equipment.get('rental_type', 'equipment')} {equipment.get('book_before_days', 'N/A')} days in advance at {equipment.get('daily_rate', 'N/A')}. "
        equipment_desc += f"Try {equipment.get('suppliers', [''])[0]} for availability."
        
        # Combine with natural flow
        parts = []
        if permit_desc:
            parts.append(permit_desc)
        parts.append(labor_desc)
        parts.append(material_desc)
        parts.append(equipment_desc)
        
        return " ".join(parts)
    
    def _assess_task_risk(self, task: dict) -> str:
        """Assess risk level for a task"""
        if not task.get("overall_available"):
            return "high"
        
        # Check for long lead times
        labor_lead = task.get("labor", {}).get("estimated_lead_time_days", 0)
        material_lead = task.get("materials", {}).get("delivery_time_days", 0)
        
        if labor_lead > 5 or material_lead > 10:
            return "medium"
        
        return "low"
    
    def _generate_mitigation_suggestions(self, task: dict) -> str:
        """Generate mitigation suggestions based on task characteristics"""
        suggestions = []
        
        if not task.get("overall_available"):
            suggestions.append("Consider alternative suppliers")
            suggestions.append("Review material substitution options")
        
        category = task.get("category", "")
        if category in ["foundation", "structural"]:
            suggestions.append("Pre-order critical materials")
            suggestions.append("Schedule quality inspections")
        
        if category in ["utilities"]:
            suggestions.append("Coordinate with utility companies early")
            suggestions.append("Ensure permit compliance")
        
        return "; ".join(suggestions) if suggestions else "Standard monitoring required"
    
    def _suggest_alternatives(self, task: dict) -> str:
        """Suggest alternative approaches"""
        category = task.get("category", "")
        
        alternatives = {
            "foundation": "Precast concrete options available",
            "structural": "Steel vs concrete alternatives",
            "utilities": "Different routing options possible",
            "finishing": "Multiple material finish options"
        }
        
        return alternatives.get(category, "Standard construction methods")
    
    def _calculate_confidence(self, task: dict) -> int:
        """Calculate confidence level for task validation"""
        base_confidence = 8 if task.get("overall_available") else 5
        
        # Adjust based on resource availability details
        labor = task.get("labor", {})
        materials = task.get("materials", {})
        equipment = task.get("equipment", {})
        
        if labor.get("available") and materials.get("available") and equipment.get("available"):
            return min(base_confidence + 1, 10)
        
        return base_confidence
    
    def get_agent(self):
        """Return the CrewAI agent for workflow integration"""
        return self.agent
