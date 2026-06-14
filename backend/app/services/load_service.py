from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.load import Load
from app.repositories.load_repository import LoadRepository
from app.schemas.load import LoadCreate, LoadProfitability, LoadResponse
from app.services.facility_service import FacilityService
from app.dependencies.fleet import get_current_fleet_id

class LoadService:
    def __init__(self, facility_service: FacilityService | None = None):
        self.load_repository = LoadRepository()
        self.facility_service = facility_service or FacilityService()

    def create_load(self, db: Session, payload: LoadCreate) -> Load:
        load = Load(**payload.model_dump())
        return self.load_repository.create(db, load)

    def get_loads(self, db: Session, fleet_id: int) -> list[LoadResponse]:
        loads = self.load_repository.get_all_by_fleet(db, fleet_id)
        facility_risk_by_load = self.facility_service.get_facility_risk_by_load_id(
            db=db, fleet_id=fleet_id, load_ids=[load.load_id for load in loads]
        )

        results = []
        for load in loads:
            response = LoadResponse.model_validate(load)
            response.facility_risk = facility_risk_by_load.get(load.load_id)
            results.append(response)

        return results

    def get_profitability(
        self,
        db: Session,
        load_id: str,
    ) -> LoadProfitability | None:
        load = self.load_repository.get_by_id(db, load_id)

        if load is None:
            return None

        revenue = Decimal(load.revenue or 0)
        miles = Decimal(load.miles or 0)
        deadhead_miles = Decimal(load.deadhead_miles or 0)
        fuel_cost = Decimal(load.fuel_cost or 0)
        maintenance_reserve = Decimal(load.maintenance_reserve or 0)
        driver_cost = Decimal(load.driver_cost or 0)
        tolls = Decimal(load.tolls or 0)

        total_cost = (
            fuel_cost
            + maintenance_reserve
            + driver_cost
            + tolls
        )

        net_profit = revenue - total_cost

        revenue_per_mile = (
            revenue / miles
            if miles > 0
            else Decimal(0)
        )

        deadhead_percentage = (
            (deadhead_miles / miles) * 100
            if miles > 0
            else Decimal(0)
        )

        return LoadProfitability(
            load_id=load.load_id,
            revenue=revenue,
            miles=miles,
            deadhead_miles=deadhead_miles,
            revenue_per_mile=round(revenue_per_mile, 2),
            deadhead_percentage=round(deadhead_percentage, 2),
            net_profit=round(net_profit, 2),
        )