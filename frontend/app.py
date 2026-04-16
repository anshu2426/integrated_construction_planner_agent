"""
Streamlit UI for Construction Planning Assistant Agent
Main application interface for the AI-powered construction planning system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
from backend.simple_crew import SimpleConstructionPlanner
from pdf_generator import prepare_pdf_data_from_results, generate_pdf
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables from .env file in parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


# Configure Streamlit page
st.set_page_config(
    page_title="Construction Planning Assistant",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_api_key():
    """Check if Groq API key is configured"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("⚠️ GROQ_API_KEY environment variable not set!")
        st.info("Please set the GROQ_API_KEY environment variable and restart the application.")
        st.code("export GROQ_API_KEY='your-api-key-here'")
        return False
    return True


def display_project_metadata(metadata):
    """Display project metadata in a formatted way"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", metadata.get("total_tasks", 0))
    
    with col2:
        duration = metadata.get("total_duration_days", 0)
        st.metric("Duration (Days)", duration)
    
    with col3:
        cost = metadata.get("total_estimated_cost", "₹0")
        st.metric("Estimated Cost", cost)
    
    with col4:
        created_date = metadata.get("created_date", "").split()[0]
        st.metric("Created", created_date)


def display_ai_insights(results):
    """Display AI-powered insights and recommendations"""
    ai_insights = results.get("ai_insights", {})
    
    if ai_insights.get("status") == "success" and ai_insights.get("ai_enhancement", False):
        st.subheader("🤖 AI Insights & Recommendations")
        
        # AI Analysis
        ai_analysis = ai_insights.get("ai_analysis", {})
        if ai_analysis:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                complexity = ai_analysis.get("project_complexity", "moderate")
                st.metric("Project Complexity", complexity.title())
            
            with col2:
                considerations = ai_analysis.get("key_considerations", [])
                st.metric("Key Considerations", len(considerations))
            
            with col3:
                risk_factors = ai_analysis.get("risk_factors", [])
                st.metric("Risk Factors", len(risk_factors))
        
        # AI Recommendations
        recommendations = ai_insights.get("ai_recommendations", [])
        if recommendations:
            st.markdown("**📋 AI Recommendations:**")
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
        
        # Enhanced Tasks
        enhanced_tasks = ai_insights.get("enhanced_tasks", [])
        if enhanced_tasks:
            st.markdown("**🔧 AI-Generated Enhanced Tasks:**")
            for task in enhanced_tasks:
                with st.expander(f"🤖 {task.get('name', 'AI Task')} ({task.get('estimated_days', 0)} days)"):
                    st.write(f"**Category:** {task.get('category', 'AI')}")
                    st.write(f"**Priority:** {task.get('priority', 'medium').title()}")
                    st.write(f"**Description:** {task.get('description', 'No description')}")
        
        # Duration Insights
        duration_insights = ai_insights.get("duration_insights", {})
        if duration_insights:
            st.markdown("**⏱️ Duration Insights:**")
            col1, col2 = st.columns(2)
            
            with col1:
                critical_tasks = duration_insights.get("critical_path_tasks", [])
                if critical_tasks:
                    st.write("**Critical Path Tasks:**")
                    for task in critical_tasks:
                        st.write(f"• {task}")
                
                potential_delays = duration_insights.get("potential_delays", [])
                if potential_delays:
                    st.write("**Potential Delays:**")
                    for delay in potential_delays:
                        st.write(f"• {delay}")
            
            with col2:
                optimizations = duration_insights.get("optimization_suggestions", [])
                if optimizations:
                    st.write("**Optimization Suggestions:**")
                    for opt in optimizations:
                        st.write(f"• {opt}")
    
    else:
        # Show fallback message
        st.info("🤖 **AI Insights**: AI enhancement is currently unavailable. Using rule-based planning only.")


def display_feature_detection(results):
    """Display feature extraction results"""
    feature_data = results.get("feature_extraction", {})
    
    st.subheader("🔍 Feature Detection Summary")
    
    if feature_data.get("has_features", False):
        # Show detected features
        features_detected = feature_data.get("features_detected", [])
        if features_detected:
            st.markdown("**✨ Detected Features:**")
            
            for feature in features_detected:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{feature['description']}**")
                
                with col2:
                    st.metric("Cost Impact", feature['cost_impact'])
                
                with col3:
                    st.metric("Days Impact", f"{feature['days_impact']}")
        
        # Show cost adjustment summary
        cost_multiplier = feature_data.get("cost_multiplier", 1.0)
        extra_days = feature_data.get("extra_days", 0)
        extra_tasks_count = feature_data.get("extra_tasks_count", 0)
        
        st.markdown("**📊 Feature Impact Summary:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cost Multiplier", f"{cost_multiplier:.2f}x")
        
        with col2:
            st.metric("Extra Days", f"{extra_days} days")
        
        with col3:
            st.metric("Extra Tasks", extra_tasks_count)
        
        # Show feature summary
        feature_summary = feature_data.get("feature_summary", "")
        if feature_summary:
            st.info(f"📋 **Summary**: {feature_summary}")
    
    else:
        st.info("🔍 **No Special Features Detected**: Using standard construction planning based on your parameters.")


def display_cost_breakdown(results):
    """Display detailed cost breakdown in INR with AI enhancements"""
    if "cost_breakdown" in results:
        cost_data = results["cost_breakdown"]
        
        st.subheader("💰 Cost Breakdown (INR)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Cost", 
                cost_data.get("total_cost", "₹0"),
                help="Total project cost including all components"
            )
            st.metric(
                "Cost per sq ft", 
                cost_data.get("cost_per_sqft", "₹0"),
                help="Base cost per square foot before location adjustment"
            )
        
        with col2:
            st.metric(
                "Labor Cost", 
                cost_data.get("labor_cost", "₹0"),
                help=f"40% of total cost - {results.get('project_metadata', {}).get('quality', 'Standard')} quality"
            )
            st.metric(
                "Material Cost", 
                cost_data.get("material_cost", "₹0"),
                help="50% of total cost - includes all construction materials"
            )
        
        with col3:
            st.metric(
                "Equipment Cost", 
                cost_data.get("equipment_cost", "₹0"),
                help="10% of total cost - equipment rental and tools"
            )
            st.metric(
                "Location Factor", 
                f"{cost_data.get('location_factor', 1.0)}x",
                help=f"Location multiplier - {results.get('project_metadata', {}).get('location', 'Tier 2')}"
            )
        
        # Show area breakdown for transparency
        st.markdown("**Area Calculation:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Ground Floor Area", 
                f"{cost_data.get('ground_floor_area', 0)} sq ft",
                help="Input area per floor"
            )
        
        with col2:
            st.metric(
                "Effective Floors", 
                cost_data.get("effective_floors", 1.0),
                help="Floor scaling factor (1 + 0.9 × (floors - 1))"
            )
        
        with col3:
            st.metric(
                "Total Built-up Area", 
                f"{cost_data.get('total_builtup_area', 0)} sq ft",
                help="Ground floor area × Effective floors"
            )
        
        # Show feature-based cost adjustments
        base_cost = cost_data.get("base_cost", "")
        cost_increase = cost_data.get("cost_increase", "")
        feature_multiplier = cost_data.get("feature_multiplier", 1.0)
        
        if base_cost and cost_increase and feature_multiplier != 1.0:
            st.markdown("**💡 Feature-Based Cost Adjustments:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Base Cost", base_cost)
            
            with col2:
                st.metric("Feature Multiplier", f"{feature_multiplier:.2f}x")
            
            with col3:
                st.metric("Cost Increase", cost_increase)
        
        # Show AI optimization tips
        ai_tips = cost_data.get("ai_optimization_tips", [])
        cost_savers = cost_data.get("potential_cost_savers", [])
        
        if ai_tips or cost_savers:
            st.markdown("**🤖 AI Cost Optimization:**")
            
            if ai_tips:
                st.write("**Optimization Tips:**")
                for tip in ai_tips:
                    st.write(f"• {tip}")
            
            if cost_savers:
                st.write("**Potential Cost Savers:**")
                for saver in cost_savers:
                    st.write(f"• {saver}")


def display_duration_breakdown(results):
    """Display detailed duration breakdown with factors and feature adjustments"""
    if "duration_breakdown" in results:
        duration_data = results["duration_breakdown"]
        
        st.subheader("📅 Duration Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Duration", f"{duration_data.get('total_days', 0)} days")
            st.metric("Foundation Phase", f"{duration_data.get('foundation_days', 0)} days")
        
        with col2:
            st.metric("Structural Phase", f"{duration_data.get('structure_days', 0)} days")
            st.metric("Finishing Phase", f"{duration_data.get('finishing_days', 0)} days")
        
        # Show calculation factors
        st.markdown("**Duration Calculation Factors:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Base Duration", 
                f"{duration_data.get('base_duration', 0)} days",
                help=f"Base timeline for {duration_data.get('building_type', 'Residential')} construction"
            )
        
        with col2:
            st.metric(
                "Floor Factor", 
                f"{duration_data.get('floor_factor', 1.0)}x",
                help="Each additional floor adds 30% time"
            )
        
        with col3:
            st.metric(
                "Area Factor", 
                f"{duration_data.get('area_factor', 1.0)}x",
                help="Area adjustment (clamped to realistic range)"
            )
        
        # Show feature-based duration adjustments
        extra_days = duration_data.get("extra_days", 0)
        duration_increase = duration_data.get("duration_increase", 0)
        
        if extra_days != 0:
            st.markdown("**💡 Feature-Based Duration Adjustments:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Extra Days", f"{extra_days} days")
            
            with col2:
                st.metric("Duration Increase", f"{duration_increase} days")
        
        # Duration per sq ft indicator
        days_per_sqft = duration_data.get('days_per_sqft', 0)
        if days_per_sqft > 0:
            st.info(f"📊 Construction Speed: {days_per_sqft:.3f} days per square foot")
        
        # Show AI duration insights
        duration_insights = duration_data.get("duration_insights", {})
        if duration_insights:
            st.markdown("**🤖 AI Duration Insights:**")
            
            critical_tasks = duration_insights.get("critical_path_tasks", [])
            potential_delays = duration_insights.get("potential_delays", [])
            optimizations = duration_insights.get("optimization_suggestions", [])
            
            if critical_tasks or potential_delays or optimizations:
                col1, col2 = st.columns(2)
                
                with col1:
                    if critical_tasks:
                        st.write("**Critical Path Tasks:**")
                        for task in critical_tasks:
                            st.write(f"• {task}")
                    
                    if potential_delays:
                        st.write("**Potential Delays:**")
                        for delay in potential_delays:
                            st.write(f"• {delay}")
                
                with col2:
                    if optimizations:
                        st.write("**Optimization Suggestions:**")
                        for opt in optimizations:
                            st.write(f"• {opt}")
        
        # Add explanation
        st.info("""
        📋 **Duration Methodology**: 
        Duration is estimated using phase-based construction modeling adjusted for floors and area, 
        based on typical Indian residential and commercial project timelines.
        - Base: 120 days (Residential) | 180 days (Commercial)
        - Floor scaling: 30% per additional floor
        - Area adjustment: 20% variation from 2,000 sq ft baseline
        - Phase distribution: Foundation 20% | Structure 50% | Finishing 30%
        """)


def display_estimation_note():
    """Display transparency note about estimation methodology"""
    st.info("""
    📋 **Cost Estimation Methodology**: 
    Cost estimates are based on standard Indian construction benchmarks and rule-based calculations.
    - Costs calculated using industry-standard rates per square foot
    - Location factors account for regional price variations  
    - Quality grades adjust material and finishing standards
    - Labor: 40% | Materials: 50% | Equipment: 10%
    """)


def display_task_breakdown(task_breakdown):
    """Display task breakdown with visualizations"""
    tasks = task_breakdown.get("tasks", [])
    
    if not tasks:
        st.warning("No tasks available")
        return
    
    st.subheader("📋 Task Overview")
    
    # Create DataFrame for visualization
    df = pd.DataFrame(tasks)
    
    # Task categories distribution
    if 'category' in df.columns:
        fig = px.pie(
            df, 
            names='category', 
            title='Task Distribution by Category',
            color_discrete_map={
                'permits': '#FF6B6B',
                'site_preparation': '#4ECDC4',
                'foundation': '#45B7D1',
                'structural': '#96CEB4',
                'utilities': '#FFEAA7',
                'finishing': '#DDA0DD'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Task duration timeline
    if 'estimated_duration_days' in df.columns and 'name' in df.columns:
        df_sorted = df.sort_values('estimated_duration_days')
        fig = px.bar(
            df_sorted,
            x='estimated_duration_days',
            y='name',
            orientation='h',
            title='Task Duration Timeline',
            color='estimated_duration_days',
            color_continuous_scale='Blues'
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed task list
    st.subheader("📝 Detailed Task List")
    
    for i, task in enumerate(tasks, 1):
        with st.expander(f"Task {i}: {task.get('name', 'Unnamed Task')} ({task.get('estimated_duration_days', 0)} days)"):
            # Task basic information
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**ID:** {task.get('id', 'N/A')}")
                st.write(f"**Category:** {task.get('category', 'N/A').title()}")
            
            with col2:
                st.write(f"**Duration:** {task.get('estimated_duration_days', 0)} days")
                dependencies = task.get('dependencies', [])
                if dependencies:
                    st.write(f"**Dependencies:** {', '.join(dependencies)}")
                else:
                    st.write("**Dependencies:** None")
            
            with col3:
                # Add phase information based on category
                category = task.get('category', '').lower()
                phase_map = {
                    'permits': 'Pre-Construction',
                    'site_preparation': 'Pre-Construction', 
                    'foundation': 'Foundation Phase',
                    'structural': 'Structural Phase',
                    'utilities': 'Structural Phase',
                    'finishing': 'Finishing Phase'
                }
                phase = phase_map.get(category, 'General')
                st.write(f"**Phase:** {phase}")
            
            # Enhanced description section
            st.markdown("---")
            st.write("**📋 Task Description:**")
            description = task.get('description', 'No description available')
            st.write(description)
            
            # Add task considerations
            if category in ['foundation', 'structural']:
                st.info("🔧 **Critical Task:** This task is on the critical path and may impact overall project timeline.")
            elif category == 'permits':
                st.info("📜 **Important:** Ensure all permits are approved before proceeding with construction.")
            elif category == 'utilities':
                st.info("⚡ **Coordination Required:** May require coordination with utility providers.")


def display_resource_validation(validation_results):
    """Display permit and booking requirements with minimalist UI"""
    validated_tasks = validation_results.get("validated_tasks", [])
    
    # Simple header
    st.subheader("📋 Permit & Booking Requirements")
    
    # Display tasks with only View Details
    for i, task in enumerate(validated_tasks, 1):
        task_name = task.get('task_name', 'Unnamed Task')
        summary = task.get('requirement_summary', 'Requirements not available')
        
        # Simple task name with expander
        with st.expander(f"{i}. {task_name}", expanded=False):
            st.write(summary)
            st.markdown("---")
            
            # Simple sections
            permits = task.get('permits_required', [])
            if permits:
                st.write("**Permits Required:**")
                for permit in permits:
                    st.write(f"- {permit.get('authority', 'N/A')} permit (submit {permit.get('submit_before_days', 'N/A')} days before, {permit.get('processing_time_days', 'N/A')} processing, fees: {permit.get('fees', 'N/A')})")
                    st.write(f"  Documents: {', '.join(permit.get('documents', []))}")
            
            labor = task.get('labor', {})
            st.write(f"**Labor:** Contact {labor.get('book_through', 'N/A')} {labor.get('contact_before_days', 'N/A')} days before (lead time: {labor.get('typical_lead_time', 'N/A')}, deposit: {labor.get('deposit', 'N/A')})")
            st.write(f"  Skills: {', '.join(labor.get('skills_required', []))}")
            
            materials = task.get('materials', {})
            st.write(f"**Materials:** Order {materials.get('supplier_type', 'N/A')} {materials.get('order_before_days', 'N/A')} days before (lead time: {materials.get('typical_lead_time', 'N/A')}, minimum: {materials.get('minimum_order', 'N/A')})")
            st.write(f"  Suppliers: {', '.join(materials.get('suppliers', []))}")
            
            equipment = task.get('equipment', {})
            st.write(f"**Equipment:** Book {equipment.get('rental_type', 'N/A')} {equipment.get('book_before_days', 'N/A')} days before (lead time: {equipment.get('typical_lead_time', 'N/A')}, rate: {equipment.get('daily_rate', 'N/A')})")
            st.write(f"  Suppliers: {', '.join(equipment.get('suppliers', []))}")


def display_project_schedule(schedule_results, validation_results=None):
    """Display project schedule with professional timeline visualization"""
    schedule = schedule_results.get("schedule", [])
    total_duration = schedule_results.get("total_project_duration", 0)
    
    st.subheader("Project Schedule")
    
    # Professional timeline visualization
    st.markdown("### Project Timeline")
    
    # Add time scale markers
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 12px; color: #666;">
            <span>Day 0</span>
            <span>Day {int(total_duration // 4)}</span>
            <span>Day {int(total_duration // 2)}</span>
            <span>Day {int(total_duration * 3 // 4)}</span>
            <span>Day {total_duration}</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Create professional timeline bars
    for task in schedule:
        task_name = task.get('task_name', 'Unnamed Task')
        start_day = task.get('start_day', 1)
        end_day = task.get('end_day', 1)
        duration = task.get('duration_days', 0)
        is_critical = task.get('critical_path', False)
        
        # Calculate progress
        start_pct = (start_day - 1) / total_duration * 100
        end_pct = end_day / total_duration * 100
        width_pct = end_pct - start_pct
        
        # Professional color scheme - muted, professional colors
        if is_critical:
            bar_color = "#C0392B"  # Dark red for critical
            bar_bg = "#E8B4B8"
        else:
            bar_color = "#2980B9"  # Dark blue for regular
            bar_bg = "#AED6F1"
        
        # Display task with timeline bar
        col1, col2 = st.columns([3, 7])
        with col1:
            # Critical indicator - simple text instead of emoji
            critical_label = "Critical" if is_critical else "Standard"
            st.markdown(f"**{task_name}**")
            st.caption(f"{critical_label} • Day {start_day}-{end_day} ({duration}d)")
        
        with col2:
            # Clean, professional timeline bar
            st.markdown(
                f"""
                <div style="
                    background: #F5F5F5; 
                    border-radius: 4px; 
                    height: 24px; 
                    position: relative; 
                    margin-top: 6px;
                    border: 1px solid #E0E0E0;
                ">
                    <div style="
                        background: {bar_color}; 
                        border-radius: 3px; 
                        height: 22px; 
                        margin-top: 1px;
                        position: absolute; 
                        left: {start_pct}%; 
                        width: {width_pct}%;
                    "></div>
                    <!-- Day markers on bar -->
                    <div style="
                        position: absolute;
                        left: {start_pct}%;
                        top: 0;
                        height: 100%;
                        width: 1px;
                        background: rgba(255,255,255,0.5);
                    "></div>
                    <div style="
                        position: absolute;
                        right: 0;
                        top: 0;
                        height: 100%;
                        width: 1px;
                        background: rgba(255,255,255,0.5);
                    "></div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    
    # Phase summary - clean and professional
    st.markdown("### Construction Phases")
    
    # Group tasks by category/phase
    phases = {
        "Foundation": [t for t in schedule if 'foundation' in t.get('task_name', '').lower() or 'excavat' in t.get('task_name', '').lower()],
        "Structural": [t for t in schedule if 'structure' in t.get('task_name', '').lower() or 'frame' in t.get('task_name', '').lower() or 'roof' in t.get('task_name', '').lower()],
        "Utilities": [t for t in schedule if 'plumbing' in t.get('task_name', '').lower() or 'electrical' in t.get('task_name', '').lower() or 'hvac' in t.get('task_name', '').lower()],
        "Finishing": [t for t in schedule if 'finishing' in t.get('task_name', '').lower() or 'install' in t.get('task_name', '').lower() or 'smart' in t.get('task_name', '').lower() or 'kitchen' in t.get('task_name', '').lower() or 'lighting' in t.get('task_name', '').lower()]
    }
    
    # Professional color palette - muted colors
    phase_colors = {
        "Foundation": "#A93226",
        "Structural": "#2E86C1",
        "Utilities": "#BA4A00",
        "Finishing": "#1E8449"
    }
    
    cols = st.columns(4)
    for idx, (phase_name, tasks) in enumerate(phases.items()):
        with cols[idx]:
            if tasks:
                color = phase_colors.get(phase_name, "#7F8C8D")
                st.markdown(
                    f"""
                    <div style="
                        background: white;
                        border: 2px solid {color};
                        border-radius: 6px;
                        padding: 16px;
                        text-align: center;
                    ">
                        <div style="font-weight: 600; font-size: 14px; color: #2C3E50;">{phase_name}</div>
                        <div style="font-size: 24px; font-weight: 700; color: {color}; margin-top: 8px;">{len(tasks)}</div>
                        <div style="font-size: 11px; color: #7F8C8D; margin-top: 4px;">Tasks</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    st.markdown("---")
    
    # Detailed timeline with deadlines
    st.markdown("### Detailed Timeline & Deadlines")
    
    for task in schedule:
        task_name = task.get('task_name', 'Unnamed Task')
        start_day = task.get('start_day', 1)
        end_day = task.get('end_day', 1)
        duration = task.get('duration_days', 0)
        is_critical = task.get('critical_path', False)
        
        with st.expander(f"{task_name} (Day {start_day}-{end_day})", expanded=False):
            # Task info card with professional styling
            border_color = "#A93226" if is_critical else "#2E86C1"
            st.markdown(
                f"""
                <div style="background: #FFFFFF; padding: 16px; border-radius: 6px; 
                            border-left: 4px solid {border_color}; border: 1px solid #E0E0E0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #7F8C8D; font-size: 12px; margin-bottom: 2px;">Duration</div>
                            <div style="font-weight: 600; font-size: 15px; color: #2C3E50;">{duration} days</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #7F8C8D; font-size: 12px; margin-bottom: 2px;">Status</div>
                            <div style="font-weight: 600; font-size: 13px; color: {border_color};">{'Critical' if is_critical else 'Standard'}</div>
                        </div>
                        <div style="text-align: right; margin-left: 20px;">
                            <div style="color: #7F8C8D; font-size: 12px; margin-bottom: 2px;">Timeline</div>
                            <div style="font-weight: 600; font-size: 13px; color: #2C3E50;">Day {start_day} - {end_day}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Show permit/booking deadlines if validation results available
            if validation_results:
                validated_tasks = validation_results.get("validated_tasks", [])
                matching_task = next((t for t in validated_tasks if t.get('task_name') == task_name), None)
                if matching_task:
                    st.markdown("#### Action Deadlines")
                    
                    permits = matching_task.get('permits_required', [])
                    labor = matching_task.get('labor', {})
                    materials = matching_task.get('materials', {})
                    
                    deadline_cols = st.columns(3)
                    
                    with deadline_cols[0]:
                        if permits:
                            permit = permits[0]
                            submit_before = permit.get('submit_before_days', 0)
                            submit_day = max(1, start_day - submit_before)
                            st.markdown(
                                f"""
                                <div style="background: #FFF9E6; padding: 14px; border-radius: 4px; 
                                            border: 1px solid #F0D43A; text-align: center;">
                                    <div style="font-weight: 600; color: #856404; font-size: 13px;">Permit</div>
                                    <div style="font-size: 13px; color: #856404; margin-top: 4px;">Submit by Day {submit_day}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    
                    with deadline_cols[1]:
                        contact_before = labor.get('contact_before_days', 0)
                        contact_day = max(1, start_day - contact_before)
                        st.markdown(
                            f"""
                            <div style="background: #E8F4F8; padding: 14px; border-radius: 4px; 
                                        border: 1px solid #B3D9E6; text-align: center;">
                                <div style="font-weight: 600; color: #0C5460; font-size: 13px;">Labor</div>
                                <div style="font-size: 13px; color: #0C5460; margin-top: 4px;">Contact by Day {contact_day}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    with deadline_cols[2]:
                        order_before = materials.get('order_before_days', 0)
                        order_day = max(1, start_day - order_before)
                        st.markdown(
                            f"""
                            <div style="background: #E8F5E9; padding: 14px; border-radius: 4px; 
                                        border: 1px solid #C8E6C9; text-align: center;">
                                <div style="font-weight: 600; color: #155724; font-size: 13px;">Materials</div>
                                <div style="font-size: 13px; color: #155724; margin-top: 4px;">Order by Day {order_day}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
    
    st.markdown("---")
    
    # Explanation section
    st.markdown("### Timeline Explanation")
    with st.expander("Understanding Your Schedule", expanded=False):
        st.markdown("""
        **Visual Timeline Bar:**
        - The colored bar shows when each task occurs in the project
        - Dark red bars indicate critical path tasks (these determine project duration)
        - Dark blue bars indicate regular tasks that can have some flexibility
        
        **Phase Cards:**
        - Foundation: Site preparation and foundation work
        - Structural: Building frame and structure
        - Utilities: Electrical, plumbing, and HVAC systems
        - Finishing: Interior work, fixtures, and smart features
        
        **Action Deadlines:**
        - Permit: When to submit permit applications
        - Labor: When to contact and book contractors
        - Materials: When to order materials to ensure timely delivery
        
        **Critical Path:**
        - Tasks marked as Critical are on the critical path
        - Delays in these tasks will delay the entire project
        - Focus extra attention on these tasks for on-time completion
        """)


def display_project_health(health_metrics):
    """Display enhanced project health and risk assessment"""
    st.subheader("🏥 Project Health Assessment")
    
    # Overall health score with color coding
    overall_score = health_metrics.get("overall_health_score", 0)
    risk_level = health_metrics.get("risk_level", "Unknown")
    
    # Color mapping for risk levels
    risk_colors = {
        "Very Low": "#10B981",  # Green
        "Low": "#34D399",      # Light Green
        "Medium": "#F59E0B",   # Orange
        "High": "#EF4444",     # Red
        "Critical": "#DC2626"  # Dark Red
    }
    risk_color = risk_colors.get(risk_level, "#6B7280")
    
    # Display overall health score prominently
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border-radius: 10px; background-color: {risk_color}20; border: 2px solid {risk_color};">
            <h2 style="color: {risk_color}; margin: 0;">Overall Health: {overall_score:.1f}/100</h2>
            <p style="color: {risk_color}; margin: 5px 0 0 0; font-weight: bold;">Risk Level: {risk_level}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detailed health dimensions
    st.markdown("### 📊 Health Dimensions")
    
    # Create progress bars for each dimension
    dimensions = [
        ("Resource Health", health_metrics.get("resource_health", 0), "Percentage of tasks with confirmed resources"),
        ("Critical Path Health", health_metrics.get("critical_path_health", 0), "Resource availability for critical tasks"),
        ("Timeline Buffer Health", health_metrics.get("timeline_buffer_health", 0), "Adequacy of project buffer time"),
        ("Permit Compliance Health", health_metrics.get("permit_compliance_health", 0), "Permit lead time adequacy"),
    ]
    
    for label, value, help_text in dimensions:
        # Determine color based on value
        if value >= 80:
            color = "#10B981"
        elif value >= 60:
            color = "#F59E0B"
        else:
            color = "#EF4444"
        
        st.markdown(f"""
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-weight: 500;">{label}</span>
                <span style="font-weight: bold; color: {color};">{value:.1f}%</span>
            </div>
            <div style="background-color: #E5E7EB; border-radius: 5px; height: 20px; overflow: hidden;">
                <div style="background-color: {color}; height: 100%; width: {value}%; transition: width 0.3s;"></div>
            </div>
            <small style="color: #6B7280;">{help_text}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Schedule confidence
    schedule_confidence = health_metrics.get("schedule_confidence", 0)
    st.markdown(f"""
    <div style="margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-weight: 500;">Schedule Confidence</span>
            <span style="font-weight: bold;">{schedule_confidence}/10</span>
        </div>
        <div style="background-color: #E5E7EB; border-radius: 5px; height: 20px; overflow: hidden;">
            <div style="background-color: #3B82F6; height: 100%; width: {schedule_confidence * 10}%; transition: width 0.3s;"></div>
        </div>
        <small style="color: #6B7280;">AI confidence in schedule feasibility</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Risk factors and recommendations in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚠️ Risk Factors")
        risk_factors = health_metrics.get("risk_factors", [])
        if risk_factors and risk_factors != ["No tasks to analyze"]:
            for i, risk in enumerate(risk_factors, 1):
                st.markdown(f"{i}. {risk}")
        else:
            st.info("No significant risk factors identified")
    
    with col2:
        st.markdown("### 💡 Recommendations")
        recommendations = health_metrics.get("recommendations", [])
        if recommendations and recommendations != ["Add tasks to enable health assessment"]:
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"{i}. {rec}")
        else:
            st.info("No specific recommendations at this time")
    
    # Metrics summary
    with st.expander("📈 Detailed Metrics"):
        metrics_summary = health_metrics.get("metrics_summary", {})
        st.json(metrics_summary)


def main():
    """Main application function"""
    # Header
    st.markdown('<h1 class="main-header">🏗️ Construction Planning Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; margin-bottom: 2rem;">AI-powered construction project planning and resource management</p>', unsafe_allow_html=True)
    
    # Check API key
    if not check_api_key():
        st.stop()
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Example goals
    example_goals = [
        "Build a residential home",
        "Construct a commercial office building",
        "Site preparation for new development",
        "Foundation planning for warehouse",
        "Permit requirements for renovation project"
    ]
    
    st.sidebar.subheader("📝 Example Goals")
    for goal in example_goals:
        if st.sidebar.button(goal):
            st.session_state.example_goal = goal
    
    # Main input section
    st.header("🎯 Project Input")
    
    # Get goal from session state or input
    if 'example_goal' in st.session_state:
        default_goal = st.session_state.example_goal
        del st.session_state.example_goal
    else:
        default_goal = ""
    
    st.subheader("📋 Project Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        area = st.number_input(
            "Total Area (sq ft)", 
            min_value=100, 
            max_value=100000, 
            value=2000, 
            step=100,
            help="Total built-up area in square feet"
        )
        
        floors = st.number_input(
            "Number of Floors", 
            min_value=1, 
            max_value=50, 
            value=2, 
            step=1,
            help="Number of floors including ground floor"
        )
        
        building_type = st.selectbox(
            "Construction Type", 
            ["Residential", "Commercial"],
            help="Type of construction project"
        )
    
    with col2:
        quality = st.selectbox(
            "Quality Grade", 
            ["Basic", "Standard", "Premium"],
            index=1,
            help="Construction quality and finishing level"
        )
        
        location = st.selectbox(
            "Location Type", 
            ["Metro", "Tier 2", "Rural"],
            index=1,
            help="Location category for cost calculation"
        )
        
        construction_goal = st.text_input(
            "Project Description (Optional):",
            placeholder="e.g., 3-bedroom house with modern amenities",
            help="Additional details about your project"
        )
    
    # Create project parameters object
    project_params = {
        "area": area,
        "floors": floors,
        "building_type": building_type,
        "quality": quality,
        "location": location,
        "description": construction_goal or f"{building_type} building - {area} sq ft, {floors} floors"
    }
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        generate_button = st.button("🚀 Generate Plan", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear Results", use_container_width=True)
    
    # Clear results
    if clear_button:
        if 'planning_results' in st.session_state:
            del st.session_state.planning_results
        st.rerun()
    
    # Generate plan
    if generate_button:
        # Comprehensive input validation
        validation_errors = []
        validation_warnings = []
        
        # 1. Basic field validation
        if not area:
            validation_errors.append("Total Area is required")
        if not floors:
            validation_errors.append("Number of Floors is required")
        
        # 2. Floor area per floor validation
        floor_area = area / floors if floors > 0 else 0
        if floor_area < 200:
            validation_errors.append(f"Floor area too small: {floor_area:.0f} sq ft per floor (minimum 200 sq ft required)")
        elif floor_area < 300:
            validation_warnings.append(f"Floor area ({floor_area:.0f} sq ft per floor) is below recommended minimum (300 sq ft)")
        
        # 3. Building type vs description mismatch
        if construction_goal:
            goal_lower = construction_goal.lower()
            if building_type == "Residential" and "commercial" in goal_lower:
                validation_warnings.append("⚠️ Description mentions 'commercial' but building type is 'Residential' - please verify")
            if building_type == "Commercial" and ("house" in goal_lower or "home" in goal_lower or "residential" in goal_lower):
                validation_warnings.append("⚠️ Description mentions 'house/home/residential' but building type is 'Commercial' - please verify")
        
        # 4. Area vs building type validation
        if building_type == "Commercial" and area < 1000:
            validation_warnings.append(f"Commercial projects typically require minimum 1000 sq ft (current: {area} sq ft)")
        if building_type == "Residential" and area > 10000:
            validation_warnings.append(f"Large residential project ({area} sq ft) - ensure adequate permits and resources")
        
        # 5. Quality vs location validation
        if quality == "Premium" and location == "Rural":
            validation_warnings.append("Premium materials may have limited availability in rural areas - consider extended timeline")
        
        # 6. Floor count validation
        if floors > 10 and building_type == "Residential":
            validation_warnings.append("Multi-story residential projects (10+ floors) require special permits and structural engineering")
        if floors > 30:
            validation_warnings.append("High-rise project (30+ floors) requires extensive planning and regulatory approvals")
        
        # Display validation results
        if validation_errors:
            st.error("❌ Validation Errors:")
            for error in validation_errors:
                st.error(f"  • {error}")
            st.stop()
        
        if validation_warnings:
            st.warning("⚠️ Validation Warnings:")
            for warning in validation_warnings:
                st.warning(f"  • {warning}")
            
            # Ask user to confirm
            if not st.checkbox("I acknowledge these warnings and want to proceed", value=False):
                st.info("Please adjust your parameters or acknowledge the warnings to continue.")
                st.stop()
        
        with st.spinner("🤖 AI Agents are working on your construction plan..."):
            try:
                # Initialize the planner
                planner = SimpleConstructionPlanner()
                
                # Execute planning workflow with project parameters
                results = planner.plan_construction_project(project_params)
                
                # Store results in session state
                st.session_state.planning_results = results
                
                if results.get("status") == "completed":
                    st.success("✅ Construction plan generated successfully!")
                else:
                    st.error("❌ Failed to generate construction plan")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Please check your API configuration and try again.")
    
    # Display results
    if 'planning_results' in st.session_state:
        results = st.session_state.planning_results
        
        if results.get("status") == "completed":
            # Project metadata
            st.header("📊 Project Overview")
            metadata = results.get("project_metadata", {})
            display_project_metadata(metadata)
            
            # Feature Detection (NEW)
            display_feature_detection(results)
            
            # Cost breakdown
            display_cost_breakdown(results)
            
            # Duration breakdown
            display_duration_breakdown(results)
            
            # AI Insights (NEW)
            display_ai_insights(results)
            
            # Estimation methodology note
            display_estimation_note()
            
            # Summary section
            summary = results.get("summary", {})
            if summary:
                st.subheader("📋 Project Summary")
                st.write(summary.get("project_overview", ""))
                
                highlights = summary.get("key_highlights", [])
                if highlights:
                    st.write("**Key Highlights:**")
                    for highlight in highlights:
                        st.write(f"• {highlight}")
            
            # Tabbed interface for detailed results
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Tasks", "✅ Validation", "📅 Schedule", "🏥 Health"])
            
            # Get validation results for schedule integration
            validation_results = results.get("resource_validation", {})
            
            with tab1:
                task_breakdown = results.get("task_breakdown", {})
                display_task_breakdown(task_breakdown)
            
            with tab2:
                display_resource_validation(validation_results)
            
            with tab3:
                schedule_results = results.get("project_schedule", {})
                display_project_schedule(schedule_results, validation_results)
            
            with tab4:
                health_metrics = results.get("project_health", {})
                display_project_health(health_metrics)
            
            # Next steps
            next_steps = summary.get("next_steps", [])
            if next_steps:
                st.header("🎯 Recommended Next Steps")
                for i, step in enumerate(next_steps, 1):
                    st.write(f"{i}. {step}")
            
            # Download results
            st.header("💾 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Download JSON"):
                    json_data = json.dumps(results, indent=2)
                    st.download_button(
                        label="Download construction_plan.json",
                        data=json_data,
                        file_name=f"construction_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            with col2:
                if st.button("📋 Download PDF Report"):
                    try:
                        # Prepare data for PDF
                        pdf_data = prepare_pdf_data_from_results(results)
                        
                        # Generate PDF
                        pdf_bytes = generate_pdf(pdf_data)
                        
                        # Download PDF
                        st.download_button(
                            label="Download construction_report.pdf",
                            data=pdf_bytes,
                            file_name=f"construction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"❌ Error generating PDF: {str(e)}")
                        st.info("Please try again or contact support if the issue persists.")
        
        else:
            # Display error
            error_info = results.get("error", {})
            st.error(f"❌ Error: {error_info.get('message', 'Unknown error')}")
            
            suggestions = results.get("fallback_suggestions", [])
            if suggestions:
                st.subheader("💡 Suggestions")
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")


if __name__ == "__main__":
    main()
