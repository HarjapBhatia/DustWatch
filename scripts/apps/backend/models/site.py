from typing import List, Literal, Optional

from pydantic import BaseModel

RiskLevel = Literal["critical", "high", "medium", "low"]
PermitStatus = Literal["registered", "unregistered", "expired"]


class ConstructionSite(BaseModel):
	id: str
	name: str
	coordinates: List[float]
	polygon: List[List[List[float]]]
	riskLevel: RiskLevel
	riskScore: float
	permitStatus: PermitStatus
	areaM2: float
	activeDays: int
	nearbySchools: int
	nearbyHospitals: int
	detectedAt: str
	lastUpdated: str
	satelliteImageBefore: Optional[str] = None
	satelliteImageAfter: Optional[str] = None
	ward: Optional[str] = None
	address: Optional[str] = None


class CityStats(BaseModel):
	totalSites: int
	critical: int
	high: int
	medium: int
	low: int
	unregistered: int
	populationExposed: int
	lastUpdated: str
