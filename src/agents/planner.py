"""
Planner Agent Module
Analyzes user questions and create plan.
Uses Google Gemini for planning.
"""

import os
import json
import google.generativeai as genai
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ExecutionPlan:
    goal: str
    steps: list
    needs_visualization: bool
    chart_type: Optional[str]
    columns_to_use: list
    aggregation: Optional[str]
    filters: Optional[Dict[str, Any]]
    raw_response: str


class PlannerAgent:
    """
    The Planner Agent (Agent 1) that analyzes user questions
    and creates structured execution plans.
    """
    EXECUTION_PLAN_SCHEMA = {
        "type": "object",
        "required": [
            "goal",
            "steps",
            "needs_visualization",
            "chart_type",
            "columns_to_use",
            "aggregation",
            "filters"
        ],
        "properties": {
            "goal": {
                "type": "string",
                "description": "Clear description of what the user wants to achieve"
            },
            "steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Step-by-step execution plan"
            },
            "needs_visualization": {
                "type": "boolean"
            },
            "chart_type": {
                "type": ["string", "null"],
                "enum": [
                    "bar",
                    "line",
                    "pie",
                    "scatter",
                    "horizontal_bar",
                    "histogram",
                    "area",
                    "count",
                    None
                ]
            },
            "columns_to_use": {
                "type": "array",
                "items": {"type": "string"}
            },
            "aggregation": {
                "type": ["string", "null"],
                "enum": ["sum", "mean", "count", "max", "min", None]
            },
            "filters": {
                "type": ["object", "null"],
                "additionalProperties": True
            }
        },
        "additionalProperties": False
    }

    SYSTEM_PROMPT = """You are a Data Analysis Planner Agent. Your role is to analyze the user's question about their data and create a clear, structured execution plan.

IMPORTANT RULES:
1. Analyze the user's natural language question carefully
2. Consider the data schema provided to understand available columns
3. Consider conversation history for context in follow-up questions
4. Create a step-by-step plan that an executor can follow
5. Determine if visualization is needed and what type

CHART TYPE GUIDELINES:
- Use "bar" for comparing categories or showing totals
- Use "horizontal_bar" for ranking (top N) or when labels are long
- Use "line" for trends over time or continuous data
- Use "pie" for showing proportions/percentages
- Use "scatter" for correlations between two numeric variables
- Use "histogram" for distributions
- Use "count" for counting occurrences of categories

CONTEXT HANDLING:
- If the user says "show that on a chart" or refers to previous results, use the conversation history
- If the user mentions "top 5" or "top 10", include proper sorting in steps
- If the user asks to compare, identify the comparison groups

Always ensure your response is valid JSON and nothing else."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Planner Agent.
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def create_plan(
        self, 
        question: str, 
        data_schema: str,
        conversation_context: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Create an execution plan for the given question.
        
        Args:
            question: User's natural language question
            data_schema: Schema of the loaded data
            conversation_context: Previous conversation for context
            
        Returns:
            ExecutionPlan object with structured plan
        """
        # Build the prompt
        prompt_parts = [
            "DATA SCHEMA:",
            data_schema,
            ""
        ]
        
        if conversation_context:
            prompt_parts.extend([
                "CONVERSATION HISTORY:",
                conversation_context,
                ""
            ])
        
        prompt_parts.extend([
            "USER QUESTION:",
            question,
            "",
            "Create an execution plan as a JSON object:"
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        try:
            # Generate the plan using Gemini (response json format)
            response = self.model.generate_content(
                [self.SYSTEM_PROMPT, full_prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                    response_mime_type="application/json",
                    response_json_schema=self.EXECUTION_PLAN_SCHEMA
                )
            )

            plan_data = json.loads(response.text) 
            
            return ExecutionPlan(
                goal=plan_data.get("goal", "Analyze the data"),
                steps=plan_data.get("steps", ["Analyze the data"]),
                needs_visualization=plan_data.get("needs_visualization", False),
                chart_type=plan_data.get("chart_type"),
                columns_to_use=plan_data.get("columns_to_use", []),
                aggregation=plan_data.get("aggregation"),
                filters=plan_data.get("filters"),
                raw_response=response_text
            )
            
        except Exception as e:
            # Return a basic plan if parsing fails
            return ExecutionPlan(
                goal=f"Answer: {question}",
                steps=["Analyze the data to answer the question"],
                needs_visualization=False,
                chart_type=None,
                columns_to_use=[],
                aggregation=None,
                filters=None,
                raw_response=str(e)
            )
    

    def format_plan_display(self, plan: ExecutionPlan) -> str:
        """
        Format the execution plan for display to user.
        
        Args:
            plan: ExecutionPlan to format
            
        Returns:
            Formatted string for display
        """
        lines = [
            f"**Goal:** {plan.goal}",
            "",
            "**Execution Steps:**"
        ]
        
        for i, step in enumerate(plan.steps, 1):
            lines.append(f"   {i}. {step}")
        
        if plan.needs_visualization:
            lines.extend([
                "",
                f"**Visualization:** {plan.chart_type or 'auto'} chart"
            ])
        
        if plan.columns_to_use:
            lines.extend([
                "",
                f"**Columns:** {', '.join(plan.columns_to_use)}"
            ])
        
        return "\n".join(lines)