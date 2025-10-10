from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.start import startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    await startup()
    # print('\n\nLifespan\n\n')
    yield
    # print('after')


app = FastAPI(lifespan=lifespan)



@app.post('/login')
def login():
    """Processes user's authentication and returns a token
    on successful authentication.

    request body:

    - username: Unique identifier for a user e.g email, 
                phone number, name

    - password:
    """
    return "ThisTokenIsFake"