from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Ініціалізація бази даних
DATABASE_URL = "sqlite:///db/ukr-analysis.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Модель таблиці стандартних імен
class StandardName(Base):
    __tablename__ = "standard_names"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    standard_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # Зв'язок з таблицею Units
    units = relationship("Unit", back_populates="standard_name", foreign_keys="[Unit.standard_name_id]")

    # Зв'язок з таблицею UnitConversions
    unit_conversions = relationship("UnitConversion", back_populates="standard_name",
                                    foreign_keys="[UnitConversion.standard_name_id]")

    # Зв'язок з таблицею синонімів
    synonyms = relationship("AnalysisSynonym", back_populates="standard_name")

# Модель таблиці синонімів
class AnalysisSynonym(Base):
    __tablename__ = "analysis_synonyms"
    id = Column(Integer, primary_key=True, index=True)
    standard_name_id = Column(Integer, ForeignKey("standard_names.id"), nullable=False)
    synonym = Column(String, nullable=False)

    # Зв'язок з таблицею стандартних імен
    standard_name = relationship("StandardName", back_populates="synonyms")

    # Унікальне обмеження для пари (standard_name_id, synonym)
    __table_args__ = (
        UniqueConstraint("standard_name_id", "synonym", name="unique_standard_name_synonym_constraint"),
    )

class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True, index=True)
    unit = Column(String, nullable=False)  # Назва одиниці
    standard_name_id = Column(Integer, ForeignKey("standard_names.id"), nullable=False)
    is_standard = Column(Boolean, default=False)  # Чи є ця одиниця стандартною для аналізу

    # Зв'язок з таблицею стандартних імен
    standard_name = relationship("StandardName", back_populates="units", foreign_keys=[standard_name_id])

    # Зв'язок з таблицею синонімів одиниць
    synonyms = relationship("UnitSynonym", back_populates="unit")

    # Унікальне обмеження для пари (standard_name_id, unit)
    __table_args__ = (
        UniqueConstraint("standard_name_id", "unit", name="unique_standard_name_unit_constraint"),
    )


class UnitSynonym(Base):
    __tablename__ = "unit_synonyms"
    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    synonym = Column(String, nullable=False)

    # Зв'язок з таблицею одиниць
    unit = relationship("Unit", back_populates="synonyms")

    # Унікальне обмеження для пари (unit_id, synonym)
    __table_args__ = (
        UniqueConstraint("unit_id", "synonym", name="unique_unit_synonym_constraint"),
    )



# Модель таблиці конверсій одиниць
class UnitConversion(Base):
    __tablename__ = "unit_conversions"
    id = Column(Integer, primary_key=True, index=True)
    from_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)  # Вихідна одиниця
    to_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)    # Цільова одиниця
    formula = Column(String, nullable=False)  # Формула конверсії
    standard_name_id = Column(Integer, ForeignKey("standard_names.id"), nullable=False)

    # Зв'язки з таблицею Units
    from_unit = relationship("Unit", foreign_keys=[from_unit_id])
    to_unit = relationship("Unit", foreign_keys=[to_unit_id])

    # Зв'язок з таблицею StandardName
    standard_name = relationship("StandardName", back_populates="unit_conversions", foreign_keys=[standard_name_id])

    # Унікальне обмеження для пари (from_unit_id, to_unit_id)
    __table_args__ = (
        UniqueConstraint("from_unit_id", "to_unit_id", name="unique_conversion_constraint"),
    )


class Dynamic(Base):
    __tablename__ = "dynamic"
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("standard_names.id"), nullable=False, unique=True)

    # Зв'язок з таблицею StandardName
    analysis = relationship("StandardName")

    # Унікальне обмеження для analysis_id, щоб уникнути дублікатів
    __table_args__ = (
        UniqueConstraint("analysis_id", name="unique_dynamic_analysis_constraint"),
    )



def init_db():
    Base.metadata.create_all(bind=engine)

