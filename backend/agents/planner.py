"""
Planner Agent for Construction Planning Assistant
Breaks down high-level construction goals into actionable tasks
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Agent
from config.llm_config import get_groq_llm_for_crewai, PLANNER_PROMPT
import json
import re


class PlannerAgent:
    """Construction Planning Expert Agent"""
    
    def __init__(self):
        self.llm = get_groq_llm_for_crewai()
        self.agent = Agent(
            role='Construction Planning Expert',
            goal='Break down high-level construction goals into detailed, actionable tasks with proper sequencing and dependencies',
            backstory="""You are a senior construction project manager with 15+ years of experience in 
            residential and commercial construction. You excel at decomposing complex construction projects 
            into manageable tasks, understanding proper sequencing, and identifying critical dependencies. 
            You're familiar with all phases of construction from permitting to final finishing.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            system_prompt=PLANNER_PROMPT
        )
    
    def create_task_breakdown(self, construction_goal: str, duration_analysis: dict = None, features: dict = None) -> dict:
        """Create a detailed task breakdown for the given construction goal"""
        import logging
        try:
            # Build enhanced prompt with duration and feature context
            prompt = self._build_enhanced_prompt(construction_goal, duration_analysis, features)
            
            # Use direct LLM call for better control
            from config.llm_config import get_groq_client
            client = get_groq_client()
            
            logging.info(f"Calling LLM for task breakdown: {construction_goal}")
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            logging.info(f"LLM response received, length: {len(content)}")
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed_result = json.loads(json_match.group())
                logging.info(f"Successfully parsed tasks: {len(parsed_result.get('tasks', []))} tasks")
                return parsed_result
            else:
                # Fallback structure
                logging.warning(f"Could not parse JSON from LLM response, using fallback. Response preview: {content[:200]}")
                return self._create_fallback_tasks(construction_goal, error="JSON parsing failed")
                
        except Exception as e:
            # Return basic structure if something goes wrong
            logging.error(f"LLM call failed: {str(e)}", exc_info=True)
            return self._create_fallback_tasks(construction_goal, error=str(e))
    
    def _build_enhanced_prompt(self, construction_goal: str, duration_analysis: dict = None, features: dict = None) -> str:
        """Build enhanced prompt with duration and feature context"""
        base_prompt = f"""
You are a construction planning expert. Break down this project into detailed tasks: "{construction_goal}"
"""
        
        if duration_analysis:
            base_prompt += f"""
Project Timeline:
- Total Duration: {duration_analysis.get('total_days', 120)} days
- Foundation Phase: {duration_analysis.get('foundation_days', 24)} days
- Structural Phase: {duration_analysis.get('structure_days', 60)} days  
- Finishing Phase: {duration_analysis.get('finishing_days', 36)} days
"""
        
        if features and features.get('has_features'):
            detected = features.get('features_detected', [])
            base_prompt += f"\nSpecial Features Detected: {', '.join([f['description'] for f in detected])}\n"
        
        base_prompt += """
Return ONLY JSON format with tasks and realistic durations:
{
  "goal": "construction goal",
  "tasks": [
    {
      "id": "task_1",
      "name": "Task name",
      "description": "Detailed, comprehensive description explaining what this task involves, materials needed, and key considerations",
      "category": "permits|site_preparation|foundation|structural|utilities|finishing",
      "estimated_duration_days": 5,
      "dependencies": []
    }
  ]
}

Create 10-12 realistic tasks with proper sequencing and detailed descriptions.

TASK DISTRIBUTION GUIDELINES:
- Permits: 1-2 tasks (5-10 days total)
- Site Preparation: 1-2 tasks (5-10 days total)
- Foundation: 2-3 tasks
- Structural: 3-4 tasks
- Utilities: 1-2 tasks (5-10 days total)
- Finishing: 2-3 tasks

DESCRIPTION REQUIREMENTS:
- Each description should be 2-3 sentences
- Explain what the task involves
- Mention key materials or equipment needed
- Include important considerations or quality checks

DO NOT include any cost estimates.
Focus on realistic construction sequencing and detailed explanations.
"""
        return base_prompt
    
    def _create_fallback_tasks(self, construction_goal: str, error: str = None) -> dict:
        """Create fallback task structure"""
        result = {
            "goal": construction_goal,
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Initial Planning",
                    "description": f"Planning and assessment for {construction_goal}",
                    "category": "permits",
                    "estimated_duration_days": 5,
                    "dependencies": []
                },
                {
                    "id": "task_2",
                    "name": "Site Preparation",
                    "description": "Clear and prepare the construction site",
                    "category": "site_preparation",
                    "estimated_duration_days": 7,
                    "dependencies": ["task_1"]
                },
                {
                    "id": "task_3",
                    "name": "Foundation Work",
                    "description": "Construct the building foundation",
                    "category": "foundation",
                    "estimated_duration_days": 14,
                    "dependencies": ["task_2"]
                },
                {
                    "id": "task_4",
                    "name": "Structural Framework",
                    "description": "Build the structural framework",
                    "category": "structural",
                    "estimated_duration_days": 21,
                    "dependencies": ["task_3"]
                },
                {
                    "id": "task_5",
                    "name": "Utilities Installation",
                    "description": "Install electrical, plumbing, and HVAC systems",
                    "category": "utilities",
                    "estimated_duration_days": 14,
                    "dependencies": ["task_4"]
                },
                {
                    "id": "task_6",
                    "name": "Finishing Work",
                    "description": "Complete interior and exterior finishing",
                    "category": "finishing",
                    "estimated_duration_days": 21,
                    "dependencies": ["task_5"]
                }
            ]
        }
        
        # Log error if present, but don't include it in response
        if error:
            import logging
            logging.warning(f"PlannerAgent using fallback tasks due to error: {error}")
            result["fallback_used"] = True
        
        return result
    
    def get_agent(self):
        """Return the CrewAI agent for workflow integration"""
        return self.agent
