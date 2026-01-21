"""
Planner Agent Module
Analyzes user questions and create plan.
Uses Google Gemini via LiteLLM proxy.
"""

import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
import openai


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
                "description": "Use exactly what the user asks for: bar, bar_chart, line, line_chart, pie, pie_chart, scatter, scatter_plot, horizontal_bar, histogram, area, box, heatmap, count, or null if no visualization needed"
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


    SYSTEM_PROMPT = f"""
You are a Data Analysis Planner Agent. Your role is to analyze the user's question about their data and create a clear, structured execution plan.

IMPORTANT RULES:
1. Analyze the user's natural language question carefully
2. Consider the data schema provided to understand available columns
3. Consider conversation history for context in follow-up questions
4. Create a step-by-step plan that an executor can follow
5. Determine if visualization is needed and what type

CHART TYPE - USE EXACTLY WHAT THE USER ASKS FOR:
- If user says "bar chart" → use "bar_chart" or "bar"
- If user says "line chart" → use "line_chart" or "line"  
- If user says "pie chart" → use "pie_chart" or "pie"
- If user says "scatter plot" or "scatter_plot" → use "scatter_plot"
- If user says "scatter" → use "scatter"
- If user says "horizontal bar" → use "horizontal_bar"
- If user says "histogram" → use "histogram"
- If user says "area chart" → use "area"
- If user says "box plot" → use "box"
- If user says "heatmap" → use "heatmap"
- If user says "count" → use "count"
- Match the user's exact terminology as closely as possible

OUTPUT CONSTRAINTS (MANDATORY):
- You MUST return a single JSON object
- The JSON MUST strictly follow this schema
- Do NOT include explanations, markdown, or comments
- Do NOT add extra fields
- Use null where a value does not apply

SCHEMA:
{json.dumps(EXECUTION_PLAN_SCHEMA, indent=2)}

Before responding, validate your output against the schema and fix any violations.
"""


    def __init__(self):
        """
        Initialize the Planner Agent.
        """
        self.api_key = os.getenv("LITELLM_API_KEY")
        self.api_base = os.getenv(
            "LITELLM_API_BASE",
            "https://litellm.koboi2026.biz.id/v1"
        )

        if not self.api_key:
            raise ValueError("LITELLM_API_KEY not found")

        self.model = "gemini/gemini-2.0-flash"
        
        # Initialize OpenAI client pointing to LiteLLM proxy
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )


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
            # Generate the plan using OpenAI client via LiteLLM proxy
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )

            raw_text = response.choices[0].message.content
            plan_data = json.loads(raw_text)

            return ExecutionPlan(
                goal=plan_data.get("goal", "Analyze the data"),
                steps=plan_data.get("steps", ["Analyze the data"]),
                needs_visualization=plan_data.get("needs_visualization", False),
                chart_type=plan_data.get("chart_type"),
                columns_to_use=plan_data.get("columns_to_use", []),
                aggregation=plan_data.get("aggregation"),
                filters=plan_data.get("filters"),
                raw_response=raw_text
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