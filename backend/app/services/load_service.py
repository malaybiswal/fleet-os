from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.load import Load
from app.repositories.load_repository import LoadRepository
from app.schemas.load import LoadCreate, LoadProfitability


class LoadService:
    def __init__(self):
        self.load_repository = LoadRepository()

    def create_load(self, db: Session, payload: LoadCreate) -> Load:
        load = Load(**payload.model_dump())
        return self.load_repository.create(db, load)

    def get_loads(self, db: Session):
        return self.load_repository.get_all(db)

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