from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    """
    Framework base model.

    Thin wrapper around Pydantic so generated apps and runtime share one import.
    """

    model_config = {
        "from_attributes": True,
    }
