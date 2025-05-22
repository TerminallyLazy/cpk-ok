from typing import TypedDict, List, Optional
from langgraph.graph import MessagesState

class HealthFacility(TypedDict):
    """A healthcare facility."""
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    rating: float
    description: Optional[str]
    facility_type: Optional[str]  # e.g., "pediatrician", "urgent_care", "hospital", "pharmacy"
    phone: Optional[str]
    hours: Optional[str]

class HealthProfile(TypedDict):
    """A child's health profile and associated healthcare facilities."""
    id: str
    child_name: str
    age: Optional[int]
    center_latitude: float
    center_longitude: float
    zoom_level: int # 13 for city, 15 for specific area
    facilities: List[HealthFacility]
    notes: Optional[str]  # Health notes, allergies, etc.

class SearchProgress(TypedDict):
    """The progress of a healthcare facility search."""
    query: str
    results: list[str]
    done: bool

class PlanningProgress(TypedDict):
    """The progress of health planning."""
    profile: HealthProfile
    done: bool

class AgentState(MessagesState):
    """The state of the healthcare assistant agent."""
    selected_profile_id: Optional[str]
    health_profiles: List[HealthProfile]
    search_progress: List[SearchProgress]
    planning_progress: List[PlanningProgress]
