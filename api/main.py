
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from models import ChatRequest, ChatResponse, HealthResponse
from chatbot import generate_reply

app = FastAPI(
    title="MemoMind Chatbot API",
    description="REST API for the MemoMind chatbot",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request data is invalid.",
                "details": [
                    {
                        "field": ".".join(
                            str(part) for part in error["loc"]
                        ),
                        "message": error["msg"],
                    }
                    for error in exc.errors()
                ],
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
            }
        },
        headers=exc.headers,
    )


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="healthy")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid4())

    try:
        reply = generate_reply(
            conversation_id=conversation_id,
            message=request.message,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        # Keep internal exception details out of the API response.
        raise HTTPException(
            status_code=502,
            detail="The chatbot service could not generate a response.",
        ) from exc

    return ChatResponse(
        conversation_id=conversation_id,
        response=reply,
    )
