"""
Ollama Client

Client for communicating with Ollama API for LLM inference.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any

import httpx
import structlog
import ollama

from .models import ChatMessage, ModelPerformanceMetrics

logger = structlog.get_logger()


class OllamaClient:
    """Client for Ollama API communication"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for model operations
        self.performance_stats: Dict[str, ModelPerformanceMetrics] = {}
        self.available_models: List[str] = []
        
    async def initialize(self):
        """Initialize the Ollama client and check connectivity"""
        try:
            # Test connection
            await self.health_check()
            
            # Load available models
            self.available_models = await self.list_available_models()
            
            logger.info("Ollama client initialized", 
                       models_count=len(self.available_models))
            
        except Exception as e:
            logger.error("Failed to initialize Ollama client", error=str(e))
            raise
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/api/version")
            return response.status_code == 200
        except Exception as e:
            logger.error("Ollama health check failed", error=str(e))
            return False
    
    async def list_available_models(self) -> List[str]:
        """List all available models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            
            logger.info("Listed available models", count=len(models))
            return models
            
        except Exception as e:
            logger.error("Failed to list models", error=str(e))
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from the Ollama registry"""
        try:
            logger.info("Starting model pull", model=model_name)
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                logger.info("Model pull progress", 
                                           model=model_name, 
                                           status=data["status"])
                        except json.JSONDecodeError:
                            continue
            
            # Update available models list
            self.available_models = await self.list_available_models()
            
            logger.info("Model pull completed", model=model_name)
            return True
            
        except Exception as e:
            logger.error("Model pull failed", model=model_name, error=str(e))
            return False
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/show",
                json={"name": model_name}
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Model {model_name} not found")
            raise
        except Exception as e:
            logger.error("Failed to get model info", model=model_name, error=str(e))
            raise
    
    async def generate(self, model: str, prompt: str, **kwargs) -> str:
        """Generate text using a model"""
        start_time = time.time()
        
        try:
            request_data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            generated_text = data.get("response", "")
            
            # Update performance stats
            execution_time = time.time() - start_time
            self._update_performance_stats(model, execution_time, len(generated_text))
            
            logger.info("Text generation completed",
                       model=model,
                       prompt_length=len(prompt),
                       response_length=len(generated_text),
                       execution_time=execution_time)
            
            return generated_text
            
        except Exception as e:
            logger.error("Text generation failed", model=model, error=str(e))
            raise
    
    async def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with a model using conversation format"""
        start_time = time.time()
        
        try:
            request_data = {
                "model": model,
                "messages": messages,
                "stream": False,
                **kwargs
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            
            # Update performance stats
            execution_time = time.time() - start_time
            self._update_performance_stats(model, execution_time, len(message_content))
            
            logger.info("Chat completion completed",
                       model=model,
                       messages_count=len(messages),
                       response_length=len(message_content),
                       execution_time=execution_time)
            
            return message_content
            
        except Exception as e:
            logger.error("Chat completion failed", model=model, error=str(e))
            raise
    
    async def embeddings(self, model: str, prompt: str) -> List[float]:
        """Generate embeddings for text"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": prompt
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("embedding", [])
            
        except Exception as e:
            logger.error("Embeddings generation failed", model=model, error=str(e))
            raise
    
    def _update_performance_stats(self, model: str, execution_time: float, tokens_generated: int):
        """Update performance statistics for a model"""
        if model not in self.performance_stats:
            self.performance_stats[model] = ModelPerformanceMetrics(
                model_name=model,
                total_requests=0,
                average_response_time=0.0,
                tokens_per_second=0.0,
                error_rate=0.0
            )
        
        stats = self.performance_stats[model]
        
        # Update running averages
        total_requests = stats.total_requests + 1
        new_avg_time = ((stats.average_response_time * stats.total_requests) + execution_time) / total_requests
        
        tokens_per_second = tokens_generated / execution_time if execution_time > 0 else 0
        new_tokens_per_sec = ((stats.tokens_per_second * stats.total_requests) + tokens_per_second) / total_requests
        
        # Update stats
        stats.total_requests = total_requests
        stats.average_response_time = new_avg_time
        stats.tokens_per_second = new_tokens_per_sec
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "available_models": self.available_models,
            "model_stats": {
                model: stats.dict() 
                for model, stats in self.performance_stats.items()
            },
            "total_requests": sum(stats.total_requests for stats in self.performance_stats.values()),
            "health_status": await self.health_check()
        }
    
    async def tactical_analysis_prompt(self, game_state: Dict[str, Any], unit_id: str) -> str:
        """Generate a tactical analysis using LLM"""
        prompt = f"""You are an expert tactical advisor for a turn-based RPG game. 
        Analyze the current battlefield situation and provide tactical recommendations.

        Current Game State:
        {json.dumps(game_state, indent=2)}

        Focus Unit: {unit_id}

        Please provide:
        1. Immediate threats to the focus unit
        2. Available tactical opportunities  
        3. Recommended next action with reasoning
        4. Alternative actions to consider
        5. Overall tactical assessment

        Be concise and focus on actionable advice."""
        
        return await self.generate("llama2:7b", prompt, temperature=0.7, max_tokens=1024)
    
    async def strategic_analysis_prompt(self, game_state: Dict[str, Any]) -> str:
        """Generate a strategic analysis using LLM"""
        prompt = f"""You are a strategic advisor for a tactical RPG game.
        Analyze the overall game situation and provide strategic guidance.

        Current Game State:
        {json.dumps(game_state, indent=2)}

        Please provide:
        1. Overall team strength assessment
        2. Victory probability and key factors
        3. Strategic phase identification (opening/midgame/endgame)
        4. Long-term strategic objectives
        5. Resource management recommendations

        Focus on big-picture strategy rather than individual unit tactics."""
        
        return await self.generate("llama2:7b", prompt, temperature=0.6, max_tokens=1024)
    
    async def decision_making_prompt(self, game_state: Dict[str, Any], unit_id: str, 
                                   available_actions: List[str], difficulty: str) -> str:
        """Generate a decision using LLM reasoning"""
        difficulty_context = {
            "easy": "Make conservative, safe decisions that minimize risk.",
            "normal": "Balance risk and reward with tactical awareness.",
            "hard": "Make aggressive, optimal decisions with strategic thinking.",
            "expert": "Use advanced tactics and consider long-term consequences."
        }
        
        prompt = f"""You are an AI player in a tactical RPG game at {difficulty} difficulty.
        {difficulty_context.get(difficulty, '')}

        Current Situation:
        {json.dumps(game_state, indent=2)}

        Your Unit: {unit_id}
        Available Actions: {', '.join(available_actions)}

        Choose the best action and explain your reasoning:
        1. State your chosen action clearly
        2. Explain why this action is optimal
        3. Consider the risks and benefits
        4. Mention alternative actions you considered

        Respond in JSON format:
        {{
            "chosen_action": "action_name",
            "parameters": {{}},
            "reasoning": "detailed explanation",
            "confidence": 0.8,
            "alternatives": ["action1", "action2"]
        }}"""
        
        return await self.generate("codellama:7b", prompt, temperature=0.5, max_tokens=512)
    
    async def evaluate_unit_prompt(self, unit_data: Dict[str, Any], battlefield_context: Dict[str, Any]) -> str:
        """Generate a unit evaluation using LLM"""
        prompt = f"""Evaluate this unit's current situation and capabilities:

        Unit Data:
        {json.dumps(unit_data, indent=2)}

        Battlefield Context:
        {json.dumps(battlefield_context, indent=2)}

        Provide evaluation scores (0.0-1.0) and explanations for:
        1. Combat Effectiveness
        2. Positional Advantage  
        3. Resource Efficiency
        4. Survival Probability
        5. Strategic Value

        Also provide specific recommendations for this unit."""
        
        return await self.generate("llama2:7b", prompt, temperature=0.6, max_tokens=768)