"""
Scheduler Agent for Construction Planning Assistant
Creates optimized execution timelines
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Agent
from config.llm_config import get_groq_llm_for_crewai, SCHEDULER_PROMPT
from datetime import datetime
from typing import Dict, Any, List
import json
import re


class SchedulerAgent:
    """Construction Scheduling Expert Agent"""
    
    def __init__(self):
        self.llm = get_groq_llm_for_crewai()
        self.agent = Agent(
            role='Construction Scheduling Expert',
            goal='Create optimized execution timeline for validated construction tasks with proper sequencing and dependency management',
            backstory="""You are a master construction scheduler with 20+ years of experience in project 
            timeline optimization. You excel at critical path analysis, resource leveling, and creating 
            realistic project schedules. You understand construction sequencing, weather considerations, 
            permit timelines, and how to optimize for both speed and quality. You're an expert at identifying 
            parallel work opportunities while maintaining safety and quality standards.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            system_prompt=SCHEDULER_PROMPT
        )
    
    def create_schedule(self, validated_tasks: list, duration_analysis: dict) -> dict:
        """Create an optimized execution schedule for validated tasks"""
        # Use algorithmic approach for reliable scheduling
        schedule = self._create_optimized_schedule(validated_tasks, duration_analysis)
        
        # Add LLM-based optimization insights
        enhanced_schedule = self._add_optimization_insights(schedule, validated_tasks)
        
        return enhanced_schedule
    
    def _create_optimized_schedule(self, validated_tasks: list, duration_analysis: dict) -> dict:
        """Create optimized schedule using dependency-based algorithm"""
        # Sort tasks respecting dependencies
        sorted_tasks = self._topological_sort(validated_tasks)
        
        schedule_tasks = []
        current_day = 1
        task_end_days = {}  # Track when each task finishes
        
        for task in sorted_tasks:
            # Calculate start day based on dependencies
            start_day = current_day
            dependencies = task.get('dependencies', [])
            
            if dependencies:
                # Find the latest end day among dependencies
                max_dep_end = 0
                for dep_id in dependencies:
                    # Find dependency task
                    dep_task = next((t for t in validated_tasks 
                                   if t.get('id') == dep_id or t.get('task_id') == dep_id), None)
                    if dep_task:
                        dep_end = task_end_days.get(dep_id, 0)
                        max_dep_end = max(max_dep_end, dep_end)
                
                start_day = max(start_day, max_dep_end + 1)
            
            # Get duration
            duration = task.get('estimated_duration_days', 5)
            end_day = start_day + duration - 1
            
            # Determine critical path
            is_critical = self._is_critical_path_task(task, validated_tasks)
            
            # Find parallel tasks
            parallel_tasks = self._find_parallel_tasks(task, sorted_tasks, start_day, end_day)
            
            schedule_task = {
                "task_id": task.get('task_id', task.get('id', '')),
                "task_name": task.get('task_name', task.get('name', '')),
                "start_day": start_day,
                "end_day": end_day,
                "duration_days": duration,
                "dependencies_completed": dependencies,
                "critical_path": is_critical,
                "parallel_tasks": parallel_tasks,
                "validation_status": task.get('validation_status', 'unknown'),
                "resource_confidence": task.get('confidence_level', 7)
            }
            
            schedule_tasks.append(schedule_task)
            task_end_days[task.get('id', task.get('task_id', ''))] = end_day
            
            # Update current day for next task
            current_day = max(current_day, end_day + 1)
        
        # Calculate project statistics
        total_duration = max([task["end_day"] for task in schedule_tasks]) if schedule_tasks else 0
        critical_path_tasks = [task["task_id"] for task in schedule_tasks if task["critical_path"]]
        
        # Ensure total duration matches deterministic analysis
        target_duration = duration_analysis.get("total_days", total_duration)
        if total_duration != target_duration:
            # Scale schedule to match target duration
            scale_factor = target_duration / total_duration if total_duration > 0 else 1
            for task in schedule_tasks:
                task["start_day"] = max(1, int(task["start_day"] * scale_factor))
                task["end_day"] = int(task["end_day"] * scale_factor)
                task["duration_days"] = max(1, int(task["duration_days"] * scale_factor))
            total_duration = target_duration
        
        return {
            "schedule": schedule_tasks,
            "total_project_duration": total_duration,
            "critical_path_tasks": critical_path_tasks,
            "schedule_created_date": datetime.now().strftime("%Y-%m-%d"),
            "optimization_level": "algorithmic"
        }
    
    def _topological_sort(self, tasks: list) -> list:
        """Sort tasks respecting dependencies using topological sort"""
        # Build dependency graph
        task_map = {task.get('id', task.get('task_id', '')): task for task in tasks}
        in_degree = {task_id: 0 for task_id in task_map}
        adj_list = {task_id: [] for task_id in task_map}
        
        for task in tasks:
            task_id = task.get('id', task.get('task_id', ''))
            dependencies = task.get('dependencies', [])
            for dep_id in dependencies:
                if dep_id in adj_list:
                    adj_list[dep_id].append(task_id)
                    in_degree[task_id] += 1
        
        # Kahn's algorithm for topological sort
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        sorted_tasks = []
        
        while queue:
            # Sort by category priority
            queue.sort(key=lambda tid: self._get_category_priority(task_map[tid].get('category', '')))
            task_id = queue.pop(0)
            sorted_tasks.append(task_map[task_id])
            
            for neighbor in adj_list[task_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Handle circular dependencies by adding remaining tasks
        remaining = [task for task in tasks if task.get('id', task.get('task_id', '')) not in [t.get('id', t.get('task_id', '')) for t in sorted_tasks]]
        sorted_tasks.extend(remaining)
        
        return sorted_tasks
    
    def _get_category_priority(self, category: str) -> int:
        """Get priority for task category"""
        priority = {
            'permits': 1,
            'site_preparation': 2,
            'foundation': 3,
            'structural': 4,
            'utilities': 5,
            'finishing': 6
        }
        return priority.get(category.lower(), 99)
    
    def _is_critical_path_task(self, task: dict, all_tasks: list) -> bool:
        """Determine if a task is on the critical path"""
        dependencies = task.get('dependencies', [])
        
        # Foundation and structural tasks are typically critical
        critical_categories = ['foundation', 'structural']
        if task.get('category') in critical_categories:
            return True
        
        # Tasks with no dependencies (starting tasks) are critical
        if not dependencies:
            return True
        
        # Tasks that many other tasks depend on are critical
        task_id = task.get('task_id', task.get('id', ''))
        dependency_count = sum(1 for t in all_tasks if task_id in t.get('dependencies', []))
        
        return dependency_count >= 2
    
    def _find_parallel_tasks(self, current_task: dict, all_tasks: list, 
                           start_day: int, end_day: int) -> list:
        """Find tasks that can be executed in parallel"""
        current_task_id = current_task.get('task_id', current_task.get('id', ''))
        current_dependencies = current_task.get('dependencies', [])
        current_category = current_task.get('category', '')
        
        parallel_tasks = []
        for task in all_tasks:
            task_id = task.get('task_id', task.get('id', ''))
            task_dependencies = task.get('dependencies', '')
            
            if (task_id != current_task_id and
                current_task_id not in task_dependencies and
                task_id not in current_dependencies and
                task.get('category') == current_category and
                task.get('overall_available', True)):
                
                parallel_tasks.append(task_id)
        
        return parallel_tasks[:2]  # Limit to 2 parallel tasks
    
    def _add_optimization_insights(self, schedule: dict, validated_tasks: list) -> dict:
        """Add LLM-based optimization insights"""
        enhancements = {
            "optimization_suggestions": self._generate_optimization_suggestions(validated_tasks),
            "risk_factors": self._identify_risk_factors(validated_tasks),
            "mitigation_strategies": self._generate_mitigation_strategies(validated_tasks),
            "weather_considerations": "Plan for weather delays in outdoor phases",
            "recommended_buffer_percentage": 10,
            "resource_leveling_opportunities": self._identify_resource_leveling(validated_tasks),
            "schedule_confidence": self._calculate_schedule_confidence(validated_tasks)
        }
        
        # Apply enhancements
        enhanced_schedule = schedule.copy()
        enhanced_schedule.update(enhancements)
        enhanced_schedule["optimization_level"] = "enhanced"
        
        # Add buffer time
        buffer_percentage = enhancements.get("recommended_buffer_percentage", 10)
        if buffer_percentage > 0:
            original_duration = enhanced_schedule["total_project_duration"]
            buffer_days = int(original_duration * buffer_percentage / 100)
            enhanced_schedule["total_project_duration_with_buffer"] = original_duration + buffer_days
            enhanced_schedule["buffer_days"] = buffer_days
        
        return enhanced_schedule
    
    def _generate_optimization_suggestions(self, tasks: list) -> list:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Check for parallelization opportunities
        categories = {}
        for task in tasks:
            cat = task.get('category', '')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(task)
        
        for cat, cat_tasks in categories.items():
            if len(cat_tasks) > 2:
                suggestions.append(f"Consider parallel execution for {cat} tasks")
        
        suggestions.append("Monitor resource availability closely")
        suggestions.append("Build buffer time for weather delays")
        
        return suggestions
    
    def _identify_risk_factors(self, tasks: list) -> list:
        """Identify potential risk factors"""
        risks = []
        
        for task in tasks:
            if not task.get("overall_available"):
                risks.append(f"Resource constraint for {task.get('name', 'task')}")
            
            if task.get('category') in ['foundation', 'structural']:
                risks.append("Critical path dependency risk")
        
        risks.append("Weather delays possible")
        risks.append("Material delivery delays")
        
        return list(set(risks))  # Remove duplicates
    
    def _generate_mitigation_strategies(self, tasks: list) -> list:
        """Generate mitigation strategies"""
        strategies = [
            "Build in buffer time",
            "Pre-order critical materials",
            "Have backup suppliers ready",
            "Regular progress reviews"
        ]
        
        return strategies
    
    def _identify_resource_leveling(self, tasks: list) -> list:
        """Identify resource leveling opportunities"""
        opportunities = []
        
        # Check for resource contention
        labor_heavy = [t for t in tasks if t.get('category') in ['structural', 'finishing']]
        if len(labor_heavy) > 3:
            opportunities.append("Level labor resources across structural and finishing phases")
        
        return opportunities
    
    def _calculate_schedule_confidence(self, tasks: list) -> int:
        """Calculate overall schedule confidence"""
        if not tasks:
            return 5
        
        approved = sum(1 for t in tasks if t.get("overall_available"))
        total = len(tasks)
        
        base_confidence = int((approved / total) * 10) if total > 0 else 5
        
        # Adjust based on task complexity
        complex_tasks = [t for t in tasks if t.get('category') in ['foundation', 'structural']]
        if len(complex_tasks) > len(tasks) * 0.5:
            base_confidence = max(base_confidence - 1, 3)
        
        return min(base_confidence, 10)
    
    def get_agent(self):
        """Return the CrewAI agent for workflow integration"""
        return self.agent
