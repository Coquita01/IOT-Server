from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    def __init__(self, entity: str, id: any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity} with id '{id}' was not found.",
        )

class AlreadyExistsException(HTTPException):
    def __init__(self, entity: str, field: str, value: any):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{entity} with {field} '{value}' already exists.",
        )

class BadRequestException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
