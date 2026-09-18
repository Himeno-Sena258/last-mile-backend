from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from app.db.database import Base


class CarLocation(Base):
    __tablename__ = "car_locations"

    car_id = Column(Integer, ForeignKey("cars.id"), primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    reported_at = Column(DateTime, nullable=False)
    received_at = Column(DateTime, nullable=False)
