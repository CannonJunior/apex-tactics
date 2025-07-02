"""
AI Service with Ollama Integration

FastAPI service that provides AI decision-making capabilities for Apex Tactics
using Ollama for LLM inference and tactical analysis.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
import uvicorn
import httpx
import ollama

from .models import (
    AIDecisionRequest, AIDecisionResponse, TacticalAnalysisRequest,
    StrategicAnalysisRequest, UnitEvaluationRequest, AIModelConfig
)
from .tactical_ai import TacticalAI
from .strategic_ai import StrategicAI
from .ollama_client import OllamaClient
from .websocket_integration import AIServiceWebSocketHandler
from .adaptive_difficulty import AdaptiveDifficultySystem
from .decision_explainer import DecisionExplainer, ExplanationLevel
from .performance_optimizer import PerformanceOptimizer, OptimizationType
from .test_ai_behaviors import AIBehaviorTester

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global AI service instances
ollama_client: Optional[OllamaClient] = None
tactical_ai: Optional[TacticalAI] = None
strategic_ai: Optional[StrategicAI] = None
websocket_handler: Optional[AIServiceWebSocketHandler] = None
difficulty_system: Optional[AdaptiveDifficultySystem] = None
decision_explainer: Optional[DecisionExplainer] = None
performance_optimizer: Optional[PerformanceOptimizer] = None
behavior_tester: Optional[AIBehaviorTester] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global ollama_client, tactical_ai, strategic_ai, websocket_handler, difficulty_system, decision_explainer, performance_optimizer, behavior_tester
    
    logger.info("Starting AI Service with Ollama")
    
    # Initialize Ollama client
    ollama_client = OllamaClient()
    await ollama_client.initialize()
    
    # Initialize AI engines
    tactical_ai = TacticalAI(ollama_client)
    strategic_ai = StrategicAI(ollama_client)
    
    # Initialize adaptive difficulty system
    difficulty_system = AdaptiveDifficultySystem()
    
    # Initialize decision explainer
    decision_explainer = DecisionExplainer()
    
    # Initialize performance optimizer
    performance_optimizer = PerformanceOptimizer({
        "cache_size": 1000,
        "cache_ttl": 600,
        "max_workers": 4,
        "batch_size": 10
    })
    
    # Initialize behavior tester
    behavior_tester = AIBehaviorTester()
    
    # Initialize WebSocket handler
    websocket_handler = AIServiceWebSocketHandler(app)
    await websocket_handler.start(port=9001)
    
    # Connect to other services
    await websocket_handler.connect_to_services()
    
    logger.info("AI Service initialized",
               models=await ollama_client.list_available_models())
    
    yield
    
    # Cleanup
    logger.info("Shutting down AI Service")
    if performance_optimizer:
        await performance_optimizer.shutdown()
    if websocket_handler:
        await websocket_handler.connection_manager.close_all_connections()
    if ollama_client:
        await ollama_client.close()

# Create FastAPI application
app = FastAPI(
    title="Apex Tactics AI Service",
    description="AI decision-making service using Ollama for tactical RPG gameplay",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    global ollama_client
    
    ollama_status = "unknown"
    if ollama_client:
        try:
            models = await ollama_client.list_available_models()
            ollama_status = "healthy" if models else "no_models"
        except Exception:
            ollama_status = "error"
    
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "1.0.0",
        "ollama_status": ollama_status
    }

# AI decision-making endpoints
@app.post("/ai/decide", response_model=AIDecisionResponse)
async def make_ai_decision(request: AIDecisionRequest) -> AIDecisionResponse:
    """Make an AI decision for a unit's turn"""
    global tactical_ai
    
    if not tactical_ai:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    
    try:
        logger.info("AI decision requested",
                   session_id=request.session_id,
                   unit_id=request.unit_id,
                   difficulty=request.difficulty_level)
        
        decision = await tactical_ai.make_decision(request)
        
        logger.info("AI decision completed",
                   session_id=request.session_id,
                   unit_id=request.unit_id,
                   action_type=decision.recommended_action.action_type,
                   confidence=decision.confidence)
        
        return decision
        
    except Exception as e:
        logger.error("AI decision failed",
                    session_id=request.session_id,
                    unit_id=request.unit_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"AI decision failed: {str(e)}")

@app.post("/ai/analyze/tactical")
async def tactical_analysis(request: TacticalAnalysisRequest):
    """Perform tactical analysis of battlefield state"""
    global tactical_ai
    
    if not tactical_ai:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    
    try:
        analysis = await tactical_ai.analyze_tactical_situation(request)
        
        logger.info("Tactical analysis completed",
                   session_id=request.session_id,
                   focus_unit=request.focus_unit_id)
        
        return analysis
        
    except Exception as e:
        logger.error("Tactical analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/ai/analyze/strategic")
async def strategic_analysis(request: StrategicAnalysisRequest):
    """Perform strategic analysis of overall game state"""
    global strategic_ai
    
    if not strategic_ai:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    
    try:
        analysis = await strategic_ai.analyze_strategic_situation(request)
        
        logger.info("Strategic analysis completed",
                   session_id=request.session_id)
        
        return analysis
        
    except Exception as e:
        logger.error("Strategic analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/ai/evaluate/unit")
async def evaluate_unit(request: UnitEvaluationRequest):
    """Evaluate a unit's capabilities and current state"""
    global tactical_ai
    
    if not tactical_ai:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    
    try:
        evaluation = await tactical_ai.evaluate_unit(request)
        
        logger.info("Unit evaluation completed",
                   session_id=request.session_id,
                   unit_id=request.unit_id)
        
        return evaluation
        
    except Exception as e:
        logger.error("Unit evaluation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

# Ollama model management
@app.get("/ai/models")
async def list_available_models():
    """List all available Ollama models"""
    global ollama_client
    
    if not ollama_client:
        raise HTTPException(status_code=500, detail="Ollama client not initialized")
    
    try:
        models = await ollama_client.list_available_models()
        return {"models": models}
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list models")

@app.post("/ai/models/pull")
async def pull_model(model_name: str, background_tasks: BackgroundTasks):
    """Pull a new model from Ollama registry"""
    global ollama_client
    
    if not ollama_client:
        raise HTTPException(status_code=500, detail="Ollama client not initialized")
    
    # Add model pulling as background task
    background_tasks.add_task(ollama_client.pull_model, model_name)
    
    return {"message": f"Started pulling model {model_name}"}

@app.get("/ai/models/{model_name}/info")
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    global ollama_client
    
    if not ollama_client:
        raise HTTPException(status_code=500, detail="Ollama client not initialized")
    
    try:
        info = await ollama_client.get_model_info(model_name)
        return info
    except Exception as e:
        logger.error("Failed to get model info", model=model_name, error=str(e))
        raise HTTPException(status_code=404, detail="Model not found")

# AI configuration endpoints
@app.get("/ai/config")
async def get_ai_config():
    """Get current AI configuration"""
    global tactical_ai, strategic_ai
    
    config = {}
    
    if tactical_ai:
        config["tactical"] = tactical_ai.get_config()
    
    if strategic_ai:
        config["strategic"] = strategic_ai.get_config()
    
    return config

@app.post("/ai/config")
async def update_ai_config(config: AIModelConfig):
    """Update AI configuration"""
    global tactical_ai, strategic_ai, ollama_client
    
    try:
        if tactical_ai and config.tactical_model:
            await tactical_ai.update_config(config.tactical_model, config.tactical_settings)
        
        if strategic_ai and config.strategic_model:
            await strategic_ai.update_config(config.strategic_model, config.strategic_settings)
        
        logger.info("AI configuration updated", config=config.dict())
        
        return {"message": "Configuration updated successfully"}
        
    except Exception as e:
        logger.error("Failed to update AI config", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update configuration")

# Real-time AI chat endpoint
@app.post("/ai/chat")
async def chat_with_ai(message: str, context: Optional[Dict[str, Any]] = None):
    """Chat with AI about game strategy or tactics"""
    global ollama_client
    
    if not ollama_client:
        raise HTTPException(status_code=500, detail="Ollama client not initialized")
    
    try:
        # Prepare system prompt for game context
        system_prompt = """You are an expert tactical advisor for the Apex Tactics RPG game.
        Provide strategic advice, explain game mechanics, and help with tactical decisions.
        Be concise and practical in your responses."""
        
        if context:
            system_prompt += f"\n\nCurrent game context: {json.dumps(context, indent=2)}"
        
        response = await ollama_client.chat(
            model="llama2:7b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
        
        return {
            "response": response,
            "context_used": context is not None
        }
        
    except Exception as e:
        logger.error("AI chat failed", error=str(e))
        raise HTTPException(status_code=500, detail="Chat request failed")

# Performance monitoring
@app.get("/ai/stats")
async def get_ai_stats():
    """Get AI service performance statistics"""
    global tactical_ai, strategic_ai, ollama_client
    
    stats = {}
    
    if tactical_ai:
        stats["tactical"] = tactical_ai.get_stats()
    
    if strategic_ai:
        stats["strategic"] = strategic_ai.get_stats()
    
    if ollama_client:
        stats["ollama"] = await ollama_client.get_stats()
    
    return stats

# Development endpoints
@app.post("/ai/test/decision")
async def test_ai_decision(test_scenario: Dict[str, Any]):
    """Test AI decision making with a custom scenario"""
    global tactical_ai
    
    if not tactical_ai:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    
    try:
        # Create a test request from the scenario
        request = AIDecisionRequest(
            session_id="test_session",
            unit_id=test_scenario.get("unit_id", "test_unit"),
            difficulty_level=test_scenario.get("difficulty", "normal"),
            constraints=test_scenario.get("constraints")
        )
        
        # Override game state for testing
        decision = await tactical_ai.make_decision(request, test_game_state=test_scenario.get("game_state"))
        
        return {
            "test_scenario": test_scenario,
            "ai_decision": decision.dict()
        }
        
    except Exception as e:
        logger.error("AI decision test failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.post("/ai/benchmark")
async def benchmark_ai_performance(iterations: int = 10):
    """Benchmark AI decision-making performance"""
    global tactical_ai
    
    if not tactical_ai:
        raise HTTPException(status_code=500, detail="AI service not initialized")
    
    try:
        results = await tactical_ai.benchmark_performance(iterations)
        
        return {
            "iterations": iterations,
            "results": results,
            "average_time": sum(r["execution_time"] for r in results) / len(results)
        }
        
    except Exception as e:
        logger.error("AI benchmark failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")

# Decision explanation endpoints
@app.get("/ai/explain/{decision_id}")
async def get_decision_explanation(decision_id: str):
    """Get explanation for a specific AI decision"""
    global decision_explainer
    
    if not decision_explainer:
        raise HTTPException(status_code=500, detail="Decision explainer not initialized")
    
    explanation = decision_explainer.get_explanation(decision_id)
    if not explanation:
        raise HTTPException(status_code=404, detail="Decision explanation not found")
    
    return explanation.dict()

@app.get("/ai/concepts/{concept_name}")
async def get_tactical_concept(concept_name: str):
    """Get details about a tactical concept"""
    global decision_explainer
    
    if not decision_explainer:
        raise HTTPException(status_code=500, detail="Decision explainer not initialized")
    
    concept_details = decision_explainer.get_concept_details(concept_name)
    if not concept_details:
        raise HTTPException(status_code=404, detail="Tactical concept not found")
    
    return concept_details

@app.get("/ai/concepts")
async def list_tactical_concepts():
    """List all available tactical concepts"""
    global decision_explainer
    
    if not decision_explainer:
        raise HTTPException(status_code=500, detail="Decision explainer not initialized")
    
    concepts = list(decision_explainer.concept_library.keys())
    return {"concepts": concepts}

@app.post("/ai/explain/decision")
async def explain_ai_decision(
    request: Dict[str, Any],
    explanation_level: ExplanationLevel = ExplanationLevel.DETAILED
):
    """Generate explanation for an AI decision"""
    global decision_explainer, tactical_ai
    
    if not decision_explainer or not tactical_ai:
        raise HTTPException(status_code=500, detail="AI services not initialized")
    
    try:
        # Extract required data from request
        decision_request = request.get("decision_request")
        decision_response = request.get("decision_response")
        battlefield_state = request.get("battlefield_state")
        personality_data = request.get("personality")
        
        if not all([decision_request, decision_response, battlefield_state]):
            raise HTTPException(status_code=400, detail="Missing required explanation data")
        
        # Note: In a real implementation, we would need to reconstruct
        # the actual objects from the request data
        # For now, return a mock explanation structure
        
        explanation = {
            "decision_id": f"exp_{int(time.time() * 1000)}",
            "session_id": decision_request.get("session_id"),
            "explanation_level": explanation_level,
            "primary_reasoning": "AI chose this action based on tactical analysis",
            "decision_factors": [
                {
                    "factor_type": "tactical",
                    "description": "Battlefield positioning analysis",
                    "weight": 0.7,
                    "confidence": 0.8
                }
            ],
            "tactical_concepts": ["positioning", "threat_assessment"],
            "player_tips": [
                "Consider unit positioning before acting",
                "Look for tactical opportunities"
            ]
        }
        
        return explanation
        
    except Exception as e:
        logger.error("Failed to generate decision explanation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")

@app.get("/ai/explain/stats")
async def get_explanation_stats():
    """Get statistics about decision explanations"""
    global decision_explainer
    
    if not decision_explainer:
        raise HTTPException(status_code=500, detail="Decision explainer not initialized")
    
    try:
        stats = decision_explainer.get_explanation_stats()
        return stats
    except Exception as e:
        logger.error("Failed to get explanation stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get stats")

@app.delete("/ai/explain/cleanup")
async def cleanup_old_explanations(max_age_hours: int = 24):
    """Clean up old decision explanations"""
    global decision_explainer
    
    if not decision_explainer:
        raise HTTPException(status_code=500, detail="Decision explainer not initialized")
    
    try:
        decision_explainer.clear_old_explanations(max_age_hours)
        return {"message": f"Cleaned up explanations older than {max_age_hours} hours"}
    except Exception as e:
        logger.error("Failed to cleanup explanations", error=str(e))
        raise HTTPException(status_code=500, detail="Cleanup failed")

# Performance optimization endpoints
@app.get("/ai/performance/stats")
async def get_performance_stats():
    """Get AI performance optimization statistics"""
    global performance_optimizer
    
    if not performance_optimizer:
        raise HTTPException(status_code=500, detail="Performance optimizer not initialized")
    
    try:
        stats = performance_optimizer.get_performance_stats()
        return stats
    except Exception as e:
        logger.error("Failed to get performance stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get performance stats")

@app.get("/ai/performance/trends")
async def get_performance_trends():
    """Get AI performance trends analysis"""
    global performance_optimizer
    
    if not performance_optimizer:
        raise HTTPException(status_code=500, detail="Performance optimizer not initialized")
    
    try:
        trends = performance_optimizer.analyze_performance_trends()
        return trends
    except Exception as e:
        logger.error("Failed to analyze performance trends", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to analyze trends")

@app.post("/ai/performance/configure")
async def configure_optimization(optimization_config: Dict[str, Any]):
    """Configure performance optimizations"""
    global performance_optimizer
    
    if not performance_optimizer:
        raise HTTPException(status_code=500, detail="Performance optimizer not initialized")
    
    try:
        for optimization_type, enabled in optimization_config.items():
            if optimization_type in OptimizationType.__members__:
                opt_type = OptimizationType(optimization_type)
                performance_optimizer.configure_optimization(opt_type, enabled)
        
        return {"message": "Optimization configuration updated", "config": optimization_config}
    except Exception as e:
        logger.error("Failed to configure optimizations", error=str(e))
        raise HTTPException(status_code=500, detail="Configuration failed")

@app.post("/ai/performance/clear-cache")
async def clear_performance_cache():
    """Clear performance optimization caches"""
    global performance_optimizer
    
    if not performance_optimizer:
        raise HTTPException(status_code=500, detail="Performance optimizer not initialized")
    
    try:
        performance_optimizer.clear_caches()
        return {"message": "Performance caches cleared"}
    except Exception as e:
        logger.error("Failed to clear caches", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to clear caches")

@app.post("/ai/performance/reset-metrics")
async def reset_performance_metrics():
    """Reset performance metrics"""
    global performance_optimizer
    
    if not performance_optimizer:
        raise HTTPException(status_code=500, detail="Performance optimizer not initialized")
    
    try:
        performance_optimizer.reset_metrics()
        return {"message": "Performance metrics reset"}
    except Exception as e:
        logger.error("Failed to reset metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reset metrics")

@app.post("/ai/performance/benchmark")
async def benchmark_optimizations(iterations: int = 100):
    """Benchmark performance optimizations"""
    global performance_optimizer, tactical_ai
    
    if not performance_optimizer or not tactical_ai:
        raise HTTPException(status_code=500, detail="AI services not initialized")
    
    try:
        # Create test scenarios
        test_scenarios = []
        for i in range(iterations):
            scenario = {
                "request_id": f"benchmark_{i}",
                "optimization_test": True,
                "iteration": i
            }
            test_scenarios.append(scenario)
        
        # Benchmark with and without optimizations
        start_time = time.time()
        
        # Test with optimizations
        optimized_results = await performance_optimizer.parallel_processor.process_parallel_decisions(test_scenarios)
        optimized_time = time.time() - start_time
        
        # Simple sequential processing for comparison
        start_time = time.time()
        sequential_results = []
        for scenario in test_scenarios:
            # Simulate processing
            time.sleep(0.001)  # 1ms per operation
            sequential_results.append({"processed": True, "id": scenario.get("request_id")})
        sequential_time = time.time() - start_time
        
        speedup = sequential_time / optimized_time if optimized_time > 0 else 1.0
        
        return {
            "iterations": iterations,
            "optimized_time": optimized_time,
            "sequential_time": sequential_time,
            "speedup": speedup,
            "optimization_efficiency": (sequential_time - optimized_time) / sequential_time if sequential_time > 0 else 0.0
        }
        
    except Exception as e:
        logger.error("Performance benchmark failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")

# AI behavior testing endpoints
@app.post("/ai/test/full-suite")
async def run_full_ai_test_suite():
    """Run comprehensive AI behavior test suite"""
    global behavior_tester
    
    if not behavior_tester:
        raise HTTPException(status_code=500, detail="Behavior tester not initialized")
    
    try:
        test_report = await behavior_tester.run_full_test_suite()
        return test_report
    except Exception as e:
        logger.error("AI test suite failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Test suite failed: {str(e)}")

@app.post("/ai/test/specific/{test_name}")
async def run_specific_ai_test(test_name: str):
    """Run a specific AI behavior test"""
    global behavior_tester
    
    if not behavior_tester:
        raise HTTPException(status_code=500, detail="Behavior tester not initialized")
    
    try:
        test_result = await behavior_tester.run_specific_test(test_name)
        return {
            "test_name": test_result.test_name,
            "passed": test_result.passed,
            "duration": test_result.duration,
            "details": test_result.details,
            "error_message": test_result.error_message
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Specific AI test failed", test_name=test_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.get("/ai/test/history")
async def get_ai_test_history():
    """Get history of AI behavior tests"""
    global behavior_tester
    
    if not behavior_tester:
        raise HTTPException(status_code=500, detail="Behavior tester not initialized")
    
    try:
        history = behavior_tester.get_test_history()
        return {"test_history": history}
    except Exception as e:
        logger.error("Failed to get test history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get test history")

@app.get("/ai/test/status")
async def get_ai_test_status():
    """Get current AI testing status and metrics"""
    global behavior_tester
    
    if not behavior_tester:
        raise HTTPException(status_code=500, detail="Behavior tester not initialized")
    
    try:
        return {
            "total_tests_run": len(behavior_tester.test_results),
            "passed_tests": sum(1 for r in behavior_tester.test_results if r.passed),
            "failed_tests": sum(1 for r in behavior_tester.test_results if not r.passed),
            "last_test_time": behavior_tester.test_results[-1].duration if behavior_tester.test_results else 0,
            "testing_available": True
        }
    except Exception as e:
        logger.error("Failed to get test status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get test status")

if __name__ == "__main__":
    uvicorn.run(
        "src.ai.service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_config=None
    )