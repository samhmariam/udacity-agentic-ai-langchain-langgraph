import os
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from tools import TOOL_KIT

load_dotenv()


ENERGY_ADVISOR_SYSTEM_INSTRUCTIONS = """You are EcoHome's Energy Advisor, an expert in
residential electricity use, solar generation, electric vehicles, HVAC systems, smart
appliances, and time-of-use pricing. Give practical, personalized recommendations that
reduce costs and environmental impact without compromising safety or essential comfort.

Use the available tools whenever current, historical, or calculated information is needed:
- Check weather before making solar-generation recommendations.
- Check electricity prices before recommending when to run flexible loads.
- Query usage and generation data before describing historical patterns.
- Search the energy knowledge base for relevant best practices.
- Use the savings calculator for numerical savings claims.

Base recommendations on the user's question and supplied household context, including
location, schedule, devices, comfort preferences, solar capacity, battery state, and
charging requirements. Never invent missing measurements or household details. State
assumptions and ask for information when its absence would materially change the answer.

Lead with a clear recommendation and specific time window when applicable. Explain how
pricing, weather, solar output, and usage history support it. Quantify savings when enough
data is available, identify uncertainty and safety constraints, and keep answers concise
and actionable.
"""


class EnergyAdvisorState(TypedDict):
    """Messages passed through the Energy Advisor workflow."""

    messages: Annotated[List[BaseMessage], add_messages]


class Agent:
    def __init__(self, instructions: Optional[str] = None, model: str = "gpt-4o-mini"):
        if not model or not model.strip():
            raise ValueError("A model name is required.")

        # Load OpenAI API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Add it to the environment or .env file."
            )

        system_instructions = ENERGY_ADVISOR_SYSTEM_INSTRUCTIONS
        custom_instructions = (instructions or "").strip()
        if custom_instructions:
            system_instructions += f"\n\nAdditional instructions:\n{custom_instructions}"

        try:
            llm = ChatOpenAI(
                model=model.strip(),
                temperature=0.0,
                api_key=api_key,
            )

            react_agent = create_agent(
                name="energy_advisor",
                system_prompt=SystemMessage(content=system_instructions),
                model=llm,
                tools=TOOL_KIT,
            )

            def run_energy_advisor(state: EnergyAdvisorState) -> EnergyAdvisorState:
                result = react_agent.invoke({"messages": state["messages"]})
                new_messages = result["messages"][len(state["messages"]):]
                return {"messages": new_messages}

            workflow = StateGraph(EnergyAdvisorState)
            workflow.add_node("energy_advisor", run_energy_advisor)
            workflow.add_edge(START, "energy_advisor")
            workflow.add_edge("energy_advisor", END)
            self.graph = workflow.compile()
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize the Energy Advisor: {exc}") from exc

    def invoke(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask the Energy Advisor a question about energy optimization.
        
        Args:
            question (str): The user's question about energy optimization
            context (str): Household or situational details used to personalize the answer
        
        Returns:
            Dict[str, Any]: Complete agent response, including messages and tool calls
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        messages = []
        normalized_context = (context or "").strip()
        if normalized_context:
            messages.append((
                "system",
                "Customer context for this request:\n"
                f"{normalized_context}\n"
                "Use these details to personalize the recommendation. Do not infer "
                "details that are not provided.",
            ))

        messages.append(("user", question.strip()))

        try:
            response = self.graph.invoke({"messages": messages})
        except Exception as exc:
            raise RuntimeError(f"Energy Advisor request failed: {exc}") from exc

        if not isinstance(response, dict) or not response.get("messages"):
            raise RuntimeError("Energy Advisor returned an invalid response without messages.")

        return response

    def get_agent_tools(self):
        """Get list of available tools for the Energy Advisor"""
        return [t.name for t in TOOL_KIT]
