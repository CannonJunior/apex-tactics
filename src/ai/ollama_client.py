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
        
        # Define default values for Ollama generate API
        defaults = {
            "stream": False,
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "max_tokens": None,  # Ollama uses 'num_predict'
            "num_predict": 128,
            "num_ctx": 2048,
            "mirostat": 0,
            "mirostat_eta": 0.1,
            "mirostat_tau": 5.0,
            "seed": None,
            "stop": None,
            "tfs_z": 1.0,
            "typical_p": 1.0,
            "repeat_last_n": 64,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        
        # Merge provided kwargs with defaults, kwargs take precedence
        final_params = defaults.copy()
        final_params.update(kwargs)
        
        # Handle max_tokens -> num_predict conversion
        if "max_tokens" in kwargs and "num_predict" not in kwargs:
            final_params["num_predict"] = kwargs["max_tokens"]
            del final_params["max_tokens"]
        elif "max_tokens" in final_params and final_params["max_tokens"] is None:
            del final_params["max_tokens"]
        
        try:
            # Build request with all parameters
            request_data = {
                "model": model,
                "prompt": prompt,
                **final_params
            }
            
            # Log comprehensive Ollama model call details
            logger.info("🤖 OLLAMA MODEL CALL",
                       model_name=model,
                       prompt=prompt[:200] + "..." if len(prompt) > 200 else prompt,
                       prompt_length=len(prompt),
                       temperature=final_params.get("temperature"),
                       max_tokens=kwargs.get("max_tokens"),
                       num_predict=final_params.get("num_predict"),
                       top_p=final_params.get("top_p"),
                       top_k=final_params.get("top_k"),
                       repeat_penalty=final_params.get("repeat_penalty"),
                       num_ctx=final_params.get("num_ctx"),
                       mirostat=final_params.get("mirostat"),
                       mirostat_eta=final_params.get("mirostat_eta"),
                       mirostat_tau=final_params.get("mirostat_tau"),
                       seed=final_params.get("seed"),
                       stop=final_params.get("stop"),
                       tfs_z=final_params.get("tfs_z"),
                       typical_p=final_params.get("typical_p"),
                       repeat_last_n=final_params.get("repeat_last_n"),
                       presence_penalty=final_params.get("presence_penalty"),
                       frequency_penalty=final_params.get("frequency_penalty"),
                       stream=final_params.get("stream"),
                       provided_args=list(kwargs.keys()),
                       default_args=[k for k in defaults.keys() if k not in kwargs],
                       api_endpoint="generate")
            
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
            
            logger.info("✅ OLLAMA RESPONSE COMPLETED",
                       model=model,
                       prompt_length=len(prompt),
                       response_length=len(generated_text),
                       execution_time=execution_time,
                       tokens_generated=len(generated_text.split()) if generated_text else 0)
            
            return generated_text
            
        except Exception as e:
            logger.error("❌ OLLAMA GENERATE FAILED", 
                        model=model, 
                        prompt_length=len(prompt),
                        error=str(e),
                        parameters=final_params)
            raise
    
    async def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with a model using conversation format"""
        start_time = time.time()
        
        # Define default values for Ollama chat API
        defaults = {
            "stream": False,
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "max_tokens": None,  # Ollama uses 'num_predict'
            "num_predict": 128,
            "num_ctx": 2048,
            "mirostat": 0,
            "mirostat_eta": 0.1,
            "mirostat_tau": 5.0,
            "seed": None,
            "stop": None,
            "tfs_z": 1.0,
            "typical_p": 1.0,
            "repeat_last_n": 64,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        
        # Merge provided kwargs with defaults, kwargs take precedence
        final_params = defaults.copy()
        final_params.update(kwargs)
        
        # Handle max_tokens -> num_predict conversion
        if "max_tokens" in kwargs and "num_predict" not in kwargs:
            final_params["num_predict"] = kwargs["max_tokens"]
            del final_params["max_tokens"]
        elif "max_tokens" in final_params and final_params["max_tokens"] is None:
            del final_params["max_tokens"]
        
        # Calculate total message length for logging
        total_message_length = sum(len(msg.get("content", "")) for msg in messages)
        messages_summary = [{"role": msg.get("role", "unknown"), "content_length": len(msg.get("content", ""))} for msg in messages]
        
        try:
            # Build request with all parameters
            request_data = {
                "model": model,
                "messages": messages,
                **final_params
            }
            
            # Log comprehensive Ollama chat call details
            logger.info("🤖 OLLAMA CHAT CALL",
                       model_name=model,
                       messages_count=len(messages),
                       total_message_length=total_message_length,
                       messages_summary=messages_summary,
                       temperature=final_params.get("temperature"),
                       max_tokens=kwargs.get("max_tokens"),
                       num_predict=final_params.get("num_predict"),
                       top_p=final_params.get("top_p"),
                       top_k=final_params.get("top_k"),
                       repeat_penalty=final_params.get("repeat_penalty"),
                       num_ctx=final_params.get("num_ctx"),
                       mirostat=final_params.get("mirostat"),
                       mirostat_eta=final_params.get("mirostat_eta"),
                       mirostat_tau=final_params.get("mirostat_tau"),
                       seed=final_params.get("seed"),
                       stop=final_params.get("stop"),
                       tfs_z=final_params.get("tfs_z"),
                       typical_p=final_params.get("typical_p"),
                       repeat_last_n=final_params.get("repeat_last_n"),
                       presence_penalty=final_params.get("presence_penalty"),
                       frequency_penalty=final_params.get("frequency_penalty"),
                       stream=final_params.get("stream"),
                       provided_args=list(kwargs.keys()),
                       default_args=[k for k in defaults.keys() if k not in kwargs],
                       api_endpoint="chat")
            
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
            
            logger.info("✅ OLLAMA CHAT COMPLETED",
                       model=model,
                       messages_count=len(messages),
                       total_input_length=total_message_length,
                       response_length=len(message_content),
                       execution_time=execution_time,
                       tokens_generated=len(message_content.split()) if message_content else 0)
            
            return message_content
            
        except Exception as e:
            logger.error("❌ OLLAMA CHAT FAILED", 
                        model=model, 
                        messages_count=len(messages),
                        total_input_length=total_message_length,
                        error=str(e),
                        parameters=final_params)
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
        logger.info("🎯 GENERATING TACTICAL ANALYSIS", 
                   unit_id=unit_id, 
                   game_state_keys=list(game_state.keys()),
                   prompt_type="tactical_analysis")
        
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
        logger.info("🧠 GENERATING STRATEGIC ANALYSIS", 
                   game_state_keys=list(game_state.keys()),
                   prompt_type="strategic_analysis")
        
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
        logger.info("🎲 GENERATING DECISION", 
                   unit_id=unit_id, 
                   difficulty=difficulty,
                   available_actions=available_actions,
                   game_state_keys=list(game_state.keys()),
                   prompt_type="decision_making")
        
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
        
        return await self.generate("llama2:7b", prompt, temperature=0.5, max_tokens=512)
    
    async def evaluate_unit_prompt(self, unit_data: Dict[str, Any], battlefield_context: Dict[str, Any]) -> str:
        """Generate a unit evaluation using LLM"""
        logger.info("📊 GENERATING UNIT EVALUATION", 
                   unit_data_keys=list(unit_data.keys()),
                   battlefield_context_keys=list(battlefield_context.keys()),
                   prompt_type="unit_evaluation")
        
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