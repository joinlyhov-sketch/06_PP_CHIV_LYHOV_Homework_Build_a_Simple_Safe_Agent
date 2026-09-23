from pydantic import BaseModel, Field


class SearchProductInput(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Product name or keyword to search for",
    )


class CheckStockInput(BaseModel):
    product_id: int = Field(
        ...,
        gt=0,
        description="ID of the product to check",
    )


class BuyProductInput(BaseModel):
    product_id: int = Field(
        ...,
        gt=0,
        description="ID of the product to purchase",
    )

    quantity: int = Field(
        ...,
        gt=0,
        le=2,
        description="Number of products to purchase, maximum 2",
    )