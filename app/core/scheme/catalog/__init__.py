"""Reference scheme definitions registry.

Includes official real schemes and synthetic demo test fixtures.
"""

from typing import Dict, List, Optional
from app.core.scheme.catalog.demo_equipment import DEMO_EQUIPMENT_SCHEME
from app.core.scheme.catalog.demo_micro_irrigation import DEMO_MICRO_IRRIGATION_SCHEME
from app.core.scheme.catalog.demo_soil import DEMO_SOIL_SCHEME
from app.core.scheme.catalog.pm_kisan import PM_KISAN_SCHEME
from app.core.scheme.catalog.pmfby import PMFBY_SCHEME
from app.core.scheme.schemas import SchemeDefinition


ALL_SCHEMES: List[SchemeDefinition] = [
    PM_KISAN_SCHEME,
    PMFBY_SCHEME,
    DEMO_MICRO_IRRIGATION_SCHEME,
    DEMO_EQUIPMENT_ASSISTANCE_SCHEME := DEMO_EQUIPMENT_SCHEME,
    DEMO_SOIL_SCHEME,
]

SCHEMES_BY_ID: Dict[str, SchemeDefinition] = {
    scheme.scheme_id: scheme for scheme in ALL_SCHEMES
}


def get_scheme_by_id(scheme_id: str) -> Optional[SchemeDefinition]:
    """Retrieve scheme definition by unique identifier."""
    return SCHEMES_BY_ID.get(scheme_id)


def get_schemes_by_category(category: str) -> List[SchemeDefinition]:
    """Retrieve all schemes matching an assistance category."""
    return [s for s in ALL_SCHEMES if s.assistance_category == category]
