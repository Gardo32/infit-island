import ollama
from config import settings
import asyncio
import json
import re
import logging
from typing import Dict, List, Optional, Union, Any

# Configure logger for LLM interactions
logger = logging.getLogger('llm.handler')

class LLMHandler:
    def __init__(self):
        self.client = ollama.AsyncClient(host=settings.OLLAMA_HOST)
        logger.info(f"LLMHandler initialized with Ollama host: {settings.OLLAMA_HOST}")

    async def ping(self):
        """Checks if the Ollama service is reachable."""
        try:
            # The ps() method is a lightweight way to check for a connection.
            logger.debug("Pinging Ollama service")
            await self.client.ps()
            logger.debug("Ollama ping successful")
            return True
        except Exception as e:
            logger.error(f"Failed to ping Ollama service: {str(e)}")
            return False

    async def get_response(self, prompt: Union[str, Dict[str, Any]], model: str = "gemma3:4b", json_format: bool = False, schema: dict = None):
        """
        Gets a response from the LLM asynchronously.
        
        Args:
            prompt: The input prompt for the LLM (string or JSON dict)
            model: The model to use
            json_format: Whether the response should be in JSON format
            schema: Optional JSON schema to include in the prompt for validation
        
        Returns:
            If json_format is True, returns a Python dict.
            Otherwise, returns a string response.
        """
        try:
            # Process the prompt if it's a dictionary
            if isinstance(prompt, dict):
                content = json.dumps(prompt, indent=2)
                logger.debug(f"Sending JSON prompt to model {model} (length: {len(content)} chars)")
                logger.debug(f"JSON prompt structure keys: {list(prompt.keys())}")
            else:
                content = prompt
                logger.debug(f"Sending string prompt to model {model} (length: {len(content)} chars)")
                
            # Log first 100 chars of content for debugging
            logger.debug(f"Prompt preview: {content[:100]}...")

            params = {
                'model': model,
                'messages': [{'role': 'user', 'content': content}]
            }
            
            if json_format:
                params['format'] = 'json'
                logger.debug("Requesting JSON format output")
                
                # If a schema is provided, include it in the prompt
                if schema:
                    schema_str = json.dumps(schema, indent=2)
                    # Append the schema to the prompt
                    schema_instruction = f"\n\nYour response must conform to this JSON schema:\n```json\n{schema_str}\n```\nEnsure your response is valid JSON with no markdown formatting."
                    params['messages'][0]['content'] += schema_instruction
                    logger.debug(f"Added JSON schema validation with {len(schema.keys())} root properties")

            logger.info(f"Sending request to Ollama model: {model}")
            response = await self.client.chat(**params)
            content = response['message']['content']
            logger.info(f"Received response from Ollama (length: {len(content)} chars)")
            
            # Process the response if JSON format is requested
            if json_format:
                # Try to extract JSON from the response if it's wrapped in markdown code blocks
                logger.debug("Attempting to extract and parse JSON from response")
                content = self._extract_json(content)
                
                try:
                    # Parse the JSON
                    parsed_content = json.loads(content)
                    logger.debug(f"Successfully parsed JSON response with keys: {list(parsed_content.keys()) if isinstance(parsed_content, dict) else 'non-dict response'}")
                    return parsed_content
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON response: {e}")
                    logger.error(f"Raw response: {content[:500]}...")  # Log first 500 chars of problematic response
                    # Return the raw content in case of parsing error
                    return content
            
            return content
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {type(e).__name__}: {str(e)}")
            return None
            
    def _extract_json(self, text):
        """Extract JSON from markdown code blocks or plain text."""
        # Try to find JSON in code blocks
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, text)
        
        if matches:
            # Take the first JSON code block found
            logger.debug("Found JSON in code block, extracting")
            return matches[0]
        # If no code blocks, return the original text
        logger.debug("No JSON code blocks found, using raw text")
        return text
        
    async def summarize_conversation(self, conversation_history: Union[str, List[Dict[str, Any]]], model: str = "gemma3:4b", json_format: bool = False):
        """
        Summarizes a conversation history.
        
        Args:
            conversation_history: The conversation text to summarize or list of message dictionaries
            model: The model to use
            json_format: Whether to return the summary in JSON format
            
        Returns:
            If json_format is True, a dict with summary data.
            Otherwise, a string with the summary.
        """
        logger.info(f"Summarizing conversation with model {model}, json_format={json_format}")
        if isinstance(conversation_history, list):
            logger.debug(f"Conversation history contains {len(conversation_history)} messages")
        else:
            logger.debug(f"Conversation history is string of length {len(conversation_history)}")
            
        if json_format:
            # Define a JSON schema for summarization
            schema = {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A concise summary of the conversation in no more than 3 sentences"
                    },
                    "key_points": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "1-3 key points from the conversation"
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral", "mixed"],
                        "description": "The overall sentiment of the conversation"
                    }
                },
                "required": ["summary", "key_points", "sentiment"]
            }
            
            # Handle different formats of conversation_history
            if isinstance(conversation_history, list):
                # Convert list of message dicts to JSON
                history_json = json.dumps(conversation_history, indent=2)
                prompt = {
                    "task": "summarize_conversation",
                    "conversation": conversation_history,
                    "format": "json",
                    "instructions": "Provide a concise summary, key points, and the overall sentiment of the conversation."
                }
            else:
                # Handle string format
                prompt = {
                    "task": "summarize_conversation",
                    "conversation": conversation_history,
                    "format": "json",
                    "instructions": "Provide a concise summary, key points, and the overall sentiment of the conversation."
                }
            
            logger.debug("Sending conversation for JSON summarization")
            return await self.get_response(prompt, model=model, json_format=True, schema=schema)
        else:
            if isinstance(conversation_history, list):
                # Convert list of message dicts to a readable string
                formatted_history = "\n".join([
                    f"{msg.get('speaker_id', 'Unknown')}: {msg.get('content', 'No content')}" 
                    for msg in conversation_history
                ])
                prompt = f"Please summarize the following conversation in no more than 3 sentences:\n\n{formatted_history}\n\nSummary:"
            else:
                prompt = f"Please summarize the following conversation in no more than 3 sentences:\n\n{conversation_history}\n\nSummary:"
                
            try:
                logger.debug("Sending conversation for text summarization")
                response = await self.client.chat(model=model, messages=[{'role': 'user', 'content': prompt}])
                logger.info("Successfully received text summarization response")
                return response['message']['content']
            except Exception as e:
                logger.error(f"Error communicating with Ollama for summarization: {str(e)}")
                return None
                
    async def retrieve_context(self, query: Union[str, Dict[str, Any]], context_data: List[Dict[str, Any]], 
                               model: str = "gemma3:4b", top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves relevant context from a list of context data based on a query.
        
        Args:
            query: The query to retrieve context for (string or JSON dict)
            context_data: List of context data dictionaries
            model: The model to use
            top_k: Number of top results to return
            
        Returns:
            List of most relevant context data dictionaries
        """
        logger.info(f"Retrieving context for query with model {model}, top_k={top_k}")
        
        if not context_data:
            logger.warning("No context data provided for retrieval")
            return []
            
        # Convert query to string if it's a dictionary
        if isinstance(query, dict):
            query_str = json.dumps(query)
            logger.debug("Query is JSON, converted to string")
        else:
            query_str = query
            logger.debug(f"Query is string of length {len(query_str)}")
        
        logger.debug(f"Context data contains {len(context_data)} items")
        
        # Prepare the prompt for context retrieval
        schema = {
            "type": "object",
            "properties": {
                "ranked_indices": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": f"Indices of the top {top_k} most relevant context items, ranked by relevance"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of why these items were selected"
                }
            },
            "required": ["ranked_indices"]
        }
        
        prompt = {
            "task": "retrieve_relevant_context",
            "query": query_str,
            "context_data": context_data,
            "instructions": f"Return the indices of the top {top_k} most relevant context items for the query. Index 0 is the first item.",
            "format": "json"
        }
        
        try:
            logger.debug("Sending context retrieval request")
            response = await self.get_response(prompt, model=model, json_format=True, schema=schema)
            
            if isinstance(response, dict) and "ranked_indices" in response:
                indices = response["ranked_indices"]
                logger.debug(f"Received ranked indices: {indices}")
                # Ensure indices are valid
                valid_indices = [i for i in indices if 0 <= i < len(context_data)]
                if len(valid_indices) != len(indices):
                    logger.warning(f"Some indices were invalid: {set(indices) - set(valid_indices)}")
                # Return the relevant context data
                result = [context_data[i] for i in valid_indices[:top_k]]
                logger.info(f"Returning {len(result)} context items")
                return result
            
            logger.warning("No valid ranked indices in response, falling back to first k items")
            fallback = context_data[:min(top_k, len(context_data))]
            return fallback  # Fallback to returning first k items
        except Exception as e:
            logger.error(f"Error retrieving context: {type(e).__name__}: {str(e)}")
            logger.warning("Falling back to first k context items")
            return context_data[:min(top_k, len(context_data))]  # Fallback to returning first k items
