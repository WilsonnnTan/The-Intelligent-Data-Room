import os
import pandas as pd
from typing import Optional, Tuple, Dict, Any

from utils.memory import ConversationMemory
from utils.data_loader import DataLoader

from .planner import PlannerAgent
from .executor import ExecutorAgent 


class AgentOrchestrator():
    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()

        self.data_loader = DataLoader()
        self.memory = ConversationMemory(max_messages=5)

        self.current_df: Optional[pd.DataFrame] = None

    def load_data(self, file_data, file_name: str) -> Tuple[bool, str]:
        """
        Load data from uploaded file.
        Set Memory and Executor df

        Args:
            file_data: File data
            file_name: Name of the uploaded file

        Returns:
            Tuple of (success, msg)
        """
        # Validate File
        file_size = file_data.getbuffer().nbytes if hasattr(file_data, 'getbuffer') else len(file_data.read())
        if hasattr(file_data, 'seek'):
            file_data.seek(0)

        is_valid, error_msg = self.data_loader.validate_file(file_name, file_size)
        
        if not is_valid:
            return False, error_msg

        success, msg, df = self.data_loader.load_file(file_data, file_name)

        if success and df is not None:
            self.current_df = df

            # Clear message for new uploaded file
            self.memory.messages = []

            # update memory
            schema = self.data_loader.get_schema(df)
            info = self.data_loader.get_dataframe_info(df)

            self.memory.set_dataframe_info(info)
            self.memory.set_data_schema(schema)

            # Pass df to executor agent
            self.executor.set_dataframe(df)

        return success, msg
    
    
    def process_query(self, question: str) -> Dict[str, Any]:
        """
        Process a user question through the multi-agent pipeline.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with results:
                - success: bool
                - answer: str
                - plan_display: str (formatted execution plan)
                - chart: Optional[go.Figure]
                - result_df: Optional[pd.DataFrame]
                - error: Optional[str]
        """
        result = {
            "success": False,
            "answer": "",
            "plan_display": "",
            "result_df": None,
            "image_path": None,
            "error": None
        }
        
        # Check if data is loaded
        if self.current_df is None:
            result["error"] = "Please upload a data file first."
            return result
        
        try:
            self.memory.add_message("user", question)
            
            # Step 1: Get plan from Planner Agent
            schema = self.data_loader.get_schema(self.current_df)
            context = self.memory.get_context()

            plan = self.planner.create_plan(
                question=question,
                data_schema=schema,
                conversation_context=context
            )

            self.last_plan = plan
            result["plan_display"] = self.planner.format_plan_display(plan)
            
            # Step 2: Execute plan with Executor Agent
            answer, result_df, image_path = self.executor.execute(
                plan=plan,
                df=self.current_df,
                question=question
            )
            
            result["success"] = True
            result["answer"] = answer
            result["result_df"] = result_df
            result["image_path"] = image_path

            # Update Memory      
            self.memory.add_message(
                "assistant", 
                content=answer,
            )

        except Exception as e:
            result["error"] = f"Error processing query: {str(e)}"
            result["answer"] = result["error"]
        
        return result
    

    def get_data_preview(self, n_rows: int = 5) -> Optional[pd.DataFrame]:
        """Get a preview of the loaded data."""
        if self.current_df is not None:
            return self.current_df.head(n_rows)
        return None
    

    # Pass method to orchestrator so main file doesnt need to call the class again
    def get_data_schema(self) -> str:
        """Get the schema of the loaded data."""
        if self.current_df is not None:
            return self.data_loader.get_schema(self.current_df)
        return "No data loaded."
    

    def get_data_info(self) -> str:
        """Get information about the loaded data."""
        if self.current_df is not None:
            return self.data_loader.get_dataframe_info(self.current_df)
        return "No data loaded."
    

    def get_conversation_history(self) -> list:
        """Get the conversation history."""
        return self.memory.messages
    

    def clear_conversation(self) -> None:
        """Clear conversation history but keep data."""
        self.memory.messages = []
        self.last_plan = None
    

    def reset(self) -> None:
        """Reset the entire state."""
        self.current_df = None
        self.last_plan = None
        self.memory.clear()
        self.executor.smart_df = None