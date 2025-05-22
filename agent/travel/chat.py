import json
from travel.state import AgentState
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from travel.search import search_for_healthcare_facilities
from travel.trips import add_health_profiles, update_health_profiles, delete_health_profiles
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from typing import cast
from langchain_core.tools import tool

@tool
def select_health_profile(profile_id: str):
    """Select a child's health profile"""
    return f"Selected health profile {profile_id}"

llm = ChatOpenAI(model="gpt-4o")
tools = [search_for_healthcare_facilities, select_health_profile]

async def chat_node(state: AgentState, config: RunnableConfig):
    """Handle chat operations"""
    llm_with_tools = llm.bind_tools(
        [
            *tools,
            add_health_profiles,
            update_health_profiles,
            delete_health_profiles,
            select_health_profile,
        ],
        parallel_tool_calls=False,
    )

    system_message = f"""
    You are "Our Kidz" healthcare assistant, designed to help parents with their children's healthcare needs.

    You can help parents by:
    - Answering general health and medical questions about children
    - Finding healthcare facilities like pediatricians, urgent care centers, hospitals, and pharmacies
    - Managing health profiles for their children
    - Providing guidance on when to seek medical care
    - Helping locate nearby healthcare services

    IMPORTANT SAFETY DISCLAIMERS:
    - Always remind parents that you are not a substitute for professional medical advice
    - For emergencies, always direct them to call 911 or go to the nearest emergency room
    - Encourage parents to consult with their child's healthcare provider for specific medical concerns
    - Never provide specific medical diagnoses or treatment recommendations

    If the user asks about finding healthcare facilities but doesn't specify a location, ask them for their location.

    When searching for healthcare facilities, use the search_for_healthcare_facilities tool to find pediatricians,
    urgent care centers, hospitals, pharmacies, and other medical facilities.

    Unless the user specifies otherwise, only use the first 10 results from the search_for_healthcare_facilities tool.

    When you add or edit a health profile, you don't need to summarize what you added. Just give a high level summary
    of the profile and the healthcare facilities you found.

    When you create or update a health profile, you should set it as the selected profile.
    If you delete a profile, try to select another profile.

    If an operation is cancelled by the user, DO NOT try to perform the operation again. Just ask what the user would like to do now
    instead.

    Current health profiles: {json.dumps(state.get('health_profiles', []))}
    """

    # Validate and clean conversation history to prevent OpenAI tool call errors
    messages = state.get("messages", [])
    cleaned_messages = []

    print(f"DEBUG: Processing {len(messages)} messages")
    for i, message in enumerate(messages):
        print(f"DEBUG: Message {i}: {type(message).__name__}")
        if isinstance(message, AIMessage) and message.tool_calls:
            print(f"DEBUG: AI message {i} has {len(message.tool_calls)} tool calls")
            # Check if this AI message with tool calls has corresponding tool responses
            has_all_tool_responses = True
            for tool_call in message.tool_calls:
                tool_call_id = tool_call["id"]
                has_response = False
                # Look for tool response after this AI message
                for j in range(i + 1, len(messages)):
                    if isinstance(messages[j], ToolMessage) and messages[j].tool_call_id == tool_call_id:
                        has_response = True
                        break
                    elif isinstance(messages[j], AIMessage):
                        # Stop looking if we hit another AI message
                        break

                if not has_response:
                    print(f"DEBUG: Tool call {tool_call_id} has no response")
                    has_all_tool_responses = False
                    break

            if has_all_tool_responses:
                cleaned_messages.append(message)
                print(f"DEBUG: Including AI message {i} (all tool calls have responses)")
            else:
                # Skip this AI message with tool calls that has no responses
                # This prevents the OpenAI API error
                print(f"DEBUG: Skipping AI message {i} with incomplete tool calls")
                continue
        else:
            cleaned_messages.append(message)
            print(f"DEBUG: Including message {i}")

    print(f"DEBUG: Cleaned messages: {len(cleaned_messages)} (was {len(messages)})")

    # calling ainvoke instead of invoke is essential to get streaming to work properly on tool calls.
    response = await llm_with_tools.ainvoke(
        [
            SystemMessage(content=system_message),
            *cleaned_messages
        ],
        config=config,
    )

    ai_message = cast(AIMessage, response)

    if ai_message.tool_calls:
        if ai_message.tool_calls[0]["name"] == "select_health_profile":
            return {
                "selected_profile_id": ai_message.tool_calls[0]["args"].get("profile_id", ""),
                "messages": [ai_message, ToolMessage(
                    tool_call_id=ai_message.tool_calls[0]["id"],
                    content="Health profile selected."
                )]
            }
        else:
            # For other tool calls (add_health_profiles, update_health_profiles, delete_health_profiles, search_for_healthcare_facilities),
            # just return the AI message. The routing system will handle tool execution
            # in the appropriate nodes (health_profiles_node, search_node) which will add the tool responses.
            return {
                "messages": [ai_message],
                "selected_profile_id": state.get("selected_profile_id", None),
                "health_profiles": state.get("health_profiles", [])
            }

    return {
        "messages": [response],
        "selected_profile_id": state.get("selected_profile_id", None),
        "health_profiles": state.get("health_profiles", [])
    }
