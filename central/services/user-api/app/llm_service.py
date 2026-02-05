"""
LLM Service - Ollama integration for intent processing
"""

import structlog
import httpx
import json
import time
from typing import Optional, Dict, Any
from app.config import settings
from app.exceptions import LLMError
from app.prometheus_metrics import record_llm_request

logger = structlog.get_logger()


class OllamaService:
    """Service for interacting with Ollama LLM"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.llm_timeout_seconds
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning("Ollama health check failed", error=str(e))
            return False
    
    async def process_intent(
        self,
        user_text: str,
        ha_context: Optional[str] = None,
        session_context: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Process user input to extract intent using LLM
        
        Args:
            user_text: User input text from edge device
            ha_context: Optional Home Assistant device/entity context
            session_context: Optional list of previous messages for context
            
        Returns:
            Dictionary with intent information:
            {
                "intent": "turn_on|turn_off|get_status|...",
                "target": {"type": "entity|device|area", "name": "..."},
                "action": "on|off|toggle|...",
                "parameters": {...},
                "confidence": 0.0-1.0,
                "response": "Human-readable response text"
            }
        """
        try:
            # Build prompt with context
            prompt = self._build_prompt(user_text, ha_context, session_context)
            
            logger.info("Processing intent with LLM", user_text=user_text[:50])
            
            start_time = time.time()
            success = False
            
            # Call Ollama API with Ministral-3 parameters
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": settings.llm_temperature,
                        }
                    },
                    timeout=self.timeout * 2  # Allow longer timeout for generation
                )
                
                if response.status_code != 200:
                    raise LLMError(f"Ollama returned status {response.status_code}")
                
                data = response.json()
                response_text = data.get("response", "").strip()
                
                # Parse LLM response to extract intent
                intent_data = self._parse_intent_response(response_text, user_text)
                
                success = True
                logger.info("Intent processed successfully", 
                           intent=intent_data.get("intent"),
                           confidence=intent_data.get("confidence"))
                
                return intent_data
                
        except httpx.TimeoutException as e:
            logger.error("Ollama timeout", user_text=user_text[:50])
            raise LLMError(f"LLM timeout: {str(e)}")
        except Exception as e:
            logger.error("Intent processing failed", error=str(e), user_text=user_text[:50])
            raise LLMError(f"Intent processing failed: {str(e)}")
        finally:
            # Record metrics
            duration = time.time() - start_time
            record_llm_request(model=self.model, duration=duration, success=success)
            raise LLMError(f"LLM timeout: {str(e)}")
        except Exception as e:
            logger.error("Intent processing failed", error=str(e), user_text=user_text[:50])
            raise LLMError(f"Intent processing failed: {str(e)}")
    
    def _build_prompt(
        self,
        user_text: str,
        ha_context: Optional[str] = None,
        session_context: Optional[list] = None,
    ) -> str:
        """
        Build prompt for LLM with context using Ministral-3 chat template
        
        Template format follows Ministral-3-3B-Instruct chat template:
        - [SYSTEM_PROMPT]...[/SYSTEM_PROMPT] for system message
        - [INST]...[/INST] for user messages
        
        Args:
            user_text: User input
            ha_context: Home Assistant context (available entities/devices)
            session_context: Previous messages in this session
            
        Returns:
            Formatted prompt string using Ministral-3 chat template
        """
        system_prompt = """You are a Home Assistant voice command interpreter specialized in Hungarian smart home control.

Your task is to understand user voice commands and convert them into structured Home Assistant intents.

You must respond ONLY with a valid JSON object (no markdown, no explanation, no code blocks) with this exact structure:
{
  "intent": "turn_on|turn_off|get_status|toggle|set_brightness|set_temperature|get_info|unknown",
  "target": {"type": "entity|device|area|unknown", "name": "entity_id_or_name_or_empty_string"},
  "action": "on|off|increase|decrease|set|unknown",
  "parameters": {},
  "confidence": 0.0-1.0,
  "response": "Response text in Hungarian to speak back to user"
}

Rules:
- Always respond with valid JSON, no extra text
- If unsure, set confidence to 0.0 and ask for clarification in the response field
- Use Hungarian language for all responses
- Keep responses concise (1-2 sentences)
- Be context-aware from previous messages"""

        # Build prompt using Ministral-3 chat template format
        prompt_parts = []
        
        # System prompt (required first)
        prompt_parts.append(f"[SYSTEM_PROMPT]{system_prompt}[/SYSTEM_PROMPT]")
        
        # Add session context (previous messages)
        if session_context and len(session_context) > 0:
            for msg in session_context[-5:]:  # Last 5 messages for context window
                if isinstance(msg, dict):
                    if msg.get("role") == "user":
                        prompt_parts.append(f"[INST]{msg.get('content', '')}[/INST]")
                    elif msg.get("role") == "assistant":
                        prompt_parts.append(msg.get('content', ''))
                else:
                    # Simple string format
                    prompt_parts.append(f"[INST]{msg}[/INST]")
        
        # Add HA context if available
        if ha_context:
            prompt_parts.append(f"[INST]Available Home Assistant entities:\n{ha_context}[/INST]")
        
        # Add current user command (last [INST] block)
        prompt_parts.append(f"[INST]{user_text}[/INST]")
        
        return "\n".join(prompt_parts)
    
    def _parse_intent_response(self, response_text: str, original_input: str) -> Dict[str, Any]:
        """
        Parse LLM JSON response into intent structure
        
        Args:
            response_text: LLM response text
            original_input: Original user input (fallback)
            
        Returns:
            Structured intent dictionary
        """
        try:
            # Try to extract JSON from response
            json_str = response_text.strip()
            
            # If response contains markdown code blocks, extract the JSON
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            intent_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["intent", "target", "confidence", "response"]
            for field in required_fields:
                if field not in intent_data:
                    intent_data[field] = None if field != "confidence" else 0.0
            
            return intent_data
            
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse LLM JSON response", 
                          response_text=response_text[:100],
                          error=str(e))
            # Return a fallback intent with low confidence
            return {
                "intent": "unknown",
                "target": {"type": "unknown", "name": ""},
                "action": "",
                "parameters": {},
                "confidence": 0.0,
                "response": "I didn't understand that command. Could you rephrase?"
            }
    
    async def generate_response(
        self,
        intent: str,
        result: str,
        user_text: str,
    ) -> str:
        """
        Generate a natural language response after executing an intent
        
        Args:
            intent: Executed intent type
            result: Result of the execution (success/error message)
            user_text: Original user text
            
        Returns:
            Natural language response string
        """
        try:
            prompt = f"""Given a Home Assistant command execution, generate a brief natural response in Hungarian.

Command intent: {intent}
Execution result: {result}
User asked: {user_text}

Provide a single sentence response to tell the user what was done. Be concise and natural."""
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=self.timeout * 2
                )
                
                if response.status_code == 200:
                    return response.json().get("response", "Kész.").strip()
                else:
                    return "Kész."
                    
        except Exception as e:
            logger.warning("Response generation failed", error=str(e))
            return "Parancs végrehajtva."


# Singleton instance
ollama_service = OllamaService()
