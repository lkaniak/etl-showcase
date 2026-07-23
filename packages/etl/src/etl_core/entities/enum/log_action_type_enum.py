from enum import Enum


class LogActionTypeEnum(Enum):
    ENGINE = "engine"
    PROCESSOR = "processor"
    EXTRACTION = "extraction"
    TRANSFORMATION = "transformation"
    LOADER = "loader"
