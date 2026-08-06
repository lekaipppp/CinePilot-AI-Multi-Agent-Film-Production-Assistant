#fastapi is the foundational blueprint used to create your main web server application
from fastapi import FastAPI


from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router


app = FastAPI(
    title="CinePilot AI API", #Configures the name of the project.
    version="1.0.0",  #Sets the current version number for your API documentation
)


#Plugs the CORSMiddleware checker directly inyo my FastAPI application pipeline.
app.add_middleware(
    CORSMiddleware,
    #allow_origins defines an allowlist of domain origins that are granted permission to make cross-origin API requests
    allow_origins= [
        "http://localhost:3000",
        "http://127.0.0.1:3000",    
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix="/api/v1",
)

@app.get("/")
async def root():
       return {"message": "CinePilot AI API is running"}
