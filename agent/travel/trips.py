from typing import cast, List
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from travel.state import AgentState, HealthProfile, HealthFacility
from copilotkit.langgraph import copilotkit_emit_message

async def health_profiles_node(state: AgentState, config: RunnableConfig): # pylint: disable=unused-argument
    """
    Lets the user know about the operations about to be performed on health profiles.
    """
    return state

async def perform_health_profiles_node(state: AgentState, config: RunnableConfig):
    """Execute health profile operations"""
    ai_message = cast(AIMessage, state["messages"][-1])

    if not isinstance(ai_message, AIMessage) or not ai_message.tool_calls:
        return state

    action_handlers = {
        "add_health_profiles": lambda args, tool_call_id: handle_add_health_profiles(state, args, tool_call_id),
        "delete_health_profiles": lambda args, tool_call_id: handle_delete_health_profiles(state, args, tool_call_id),
        "update_health_profiles": lambda args, tool_call_id: handle_update_health_profiles(state, args, tool_call_id),
    }

    # Initialize the health_profiles list if it doesn't exist
    if not state.get("health_profiles"):
        state["health_profiles"] = []

    for tool_call in ai_message.tool_calls:
        action = tool_call["name"]
        args = tool_call.get("args", {})
        tool_call_id = tool_call["id"]

        if action in action_handlers:
            tool_message = action_handlers[action](args, tool_call_id)
            state["messages"].append(tool_message)
            await copilotkit_emit_message(config, tool_message.content)

    return state

@tool
def add_health_profiles(health_profiles: List[HealthProfile]):
    """Add one or many health profiles to the list"""

def handle_add_health_profiles(state: AgentState, args: dict, tool_call_id: str) -> ToolMessage:
    health_profiles = args.get("health_profiles", [])

    state["health_profiles"].extend(health_profiles)
    return ToolMessage(
        tool_call_id=tool_call_id,
        content=f"Successfully added the health profile(s)!"
    )

@tool
def delete_health_profiles(profile_ids: List[str]):
    """Delete one or many health profiles. YOU MUST NOT CALL this tool multiple times in a row!"""

def handle_delete_health_profiles(state: AgentState, args: dict, tool_call_id: str) -> ToolMessage:
    profile_ids = args.get("profile_ids", [])

    # Clear selected_profile if it's being deleted
    if state.get("selected_profile_id") and state["selected_profile_id"] in profile_ids:
        state["selected_profile_id"] = None

    state["health_profiles"] = [profile for profile in state["health_profiles"] if profile["id"] not in profile_ids]
    return ToolMessage(
        tool_call_id=tool_call_id,
        content=f"Successfully deleted the health profile(s)!"
    )

@tool
def update_health_profiles(health_profiles: List[HealthProfile]):
    """Update one or many health profiles"""

def handle_update_health_profiles(state: AgentState, args: dict, tool_call_id: str) -> ToolMessage:
    health_profiles = args.get("health_profiles", [])
    for profile in health_profiles:
        state["health_profiles"] = [
            {**existing_profile, **profile} if existing_profile["id"] == profile["id"] else existing_profile
            for existing_profile in state["health_profiles"]
        ]
    return ToolMessage(
        tool_call_id=tool_call_id,
        content=f"Successfully updated the health profile(s)!"
    )

# Keep the old trip functions for backward compatibility during transition
async def trips_node(state: AgentState, config: RunnableConfig):
    """Redirect to health profiles node"""
    return await health_profiles_node(state, config)

async def perform_trips_node(state: AgentState, config: RunnableConfig):
    """Redirect to health profiles node"""
    return await perform_health_profiles_node(state, config)
