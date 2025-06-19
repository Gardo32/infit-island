import asyncio
import logging
from engine.ai import LLMHandler
from logging_config import configure_logging

# Configure logging
configure_logging()

# Create a logger for this script
logger = logging.getLogger('test_llm')

async def test_llm_handler():
    logger.info("Creating LLM handler...")
    handler = LLMHandler()
    
    # Test JSON input
    prompt = {
        "test": "message",
        "instruction": "Return a greeting"
    }
    
    logger.info("Testing with JSON input...")
    result = await handler.get_response(prompt, json_format=True)
    logger.info(f"Result: {result}")
    
    # Test string input with JSON output
    logger.info("Testing with string input and JSON output...")
    result2 = await handler.get_response("Say hello in JSON format", json_format=True)
    logger.info(f"Result: {result2}")
    
    # Test the retrieve_context method
    logger.info("Testing retrieve_context...")
    context_data = [
        {"id": 1, "content": "This is about dogs"},
        {"id": 2, "content": "This is about cats"},
        {"id": 3, "content": "This is about programming"},
        {"id": 4, "content": "This is about Python"}
    ]
    
    retrieved = await handler.retrieve_context("Tell me about programming", context_data)
    logger.info(f"Retrieved context: {retrieved}")
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_llm_handler())
