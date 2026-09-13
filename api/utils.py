from fastapi import HTTPException

def raise_not_found(detail: str = "Not found"):
    raise HTTPException(status_code=404, detail=detail)
