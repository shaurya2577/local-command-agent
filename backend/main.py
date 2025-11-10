from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional, Dict, Any
import logging

from nlu_service import NLUService
from command_runner import CommandRunner
from rag_store import RAGStore
from script_generator import ScriptGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Local Command Agent API")

# CORS for electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# init services
nlu = NLUService()
rag = RAGStore()
runner = CommandRunner()
generator = ScriptGenerator()

class CommandRequest(BaseModel):
    query: str
    auto_execute: bool = False

class CommandResponse(BaseModel):
    intent: Dict[str, Any]
    matched_command: Optional[str] = None
    script_path: Optional[str] = None
    executed: bool = False
    output: Optional[str] = None
    generated: bool = False

@app.get("/")
async def root():
    return {"status": "running", "service": "lca-backend"}

@app.post("/command", response_model=CommandResponse)
async def process_command(req: CommandRequest):
    """main endpoint for processing natural language commands"""
    try:
        # step 1: parse intent
        logger.info(f"parsing query: {req.query}")
        intent = nlu.parse_intent(req.query)
        logger.info(f"intent parsed: {intent}")

        # step 2: search rag for matching command
        match = rag.find_matching_command(intent, threshold=0.85)

        response = CommandResponse(intent=intent)

        if match:
            # found existing command
            logger.info(f"matched command: {match['name']}")
            response.matched_command = match['name']
            response.script_path = match['file_path']

            if req.auto_execute:
                # run it
                result = runner.execute_script(match['file_path'], intent)
                response.executed = True
                response.output = result
                rag.increment_usage(match['name'])
        else:
            # no match - generate new script
            logger.info("no match found, generating new script...")
            script_path = generator.generate_script(intent)

            if script_path:
                response.generated = True
                response.script_path = script_path

                # add to rag
                rag.add_command(
                    name=intent.get('action', 'unknown'),
                    description=req.query,
                    file_path=script_path
                )

                if req.auto_execute:
                    result = runner.execute_script(script_path, intent)
                    response.executed = True
                    response.output = result

        return response

    except Exception as e:
        logger.error(f"error processing command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/commands")
async def list_commands():
    """list all available commands"""
    return rag.list_all_commands()

@app.get("/history")
async def get_history(limit: int = 10):
    """get recent command history"""
    return rag.get_history(limit)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
