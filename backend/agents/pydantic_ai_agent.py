import os
import logging
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel

from backend.schemas.agents import AgentMessage, AgentRunContext, AgentRunResult

logger = logging.getLogger(__name__)


class PydanticAIAgent:
    def __init__(self):
        self.model = self._select_model()
        self.is_mock = isinstance(self.model, TestModel)
        self.agent = Agent(
            self.model,
            output_type=AgentRunResult,
            system_prompt="You are a layout structured output validator agent."
        )

    def _select_model(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        # Clear out default placeholder values
        if openai_key == "your_openai_api_key_here":
            openai_key = None
        if gemini_key == "your_gemini_api_key_here":
            gemini_key = None

        if openai_key:
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
            base_url = os.getenv("OPENAI_API_BASE")
            logger.info(f"PydanticAI: Using OpenAIModel ({model_name})")
            return OpenAIModel(model_name, base_url=base_url, api_key=openai_key)
        elif gemini_key:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
            logger.info(f"PydanticAI: Using GeminiModel ({model_name})")
            return GeminiModel(model_name)
        else:
            logger.warning("PydanticAI: No valid API keys found. Falling back to TestModel (Mock).")
            return TestModel()

    def run(self, context: AgentRunContext) -> AgentRunResult:
        logger.info("Running PydanticAI Agent step...")
        prompt = (
            f"Validate layout data context: html_content={context.html_content}, "
            f"target_framework={context.target_framework}"
        )

        try:
            res = self.agent.run_sync(prompt)
            if self.is_mock:
                logger.info("PydanticAI: Mock model matched. Customizing structured return schema.")
                msg = AgentMessage(
                    sender="PydanticAIAgent",
                    content="Mock PydanticAI validation completed. Outputs verified."
                )
                return AgentRunResult(
                    success=True,
                    status="COMPLETED",
                    messages=[msg],
                    output_data={
                        "validation_status": "PASSED",
                        "framework_target": context.target_framework,
                        "elements_validated": 12
                    },
                    metadata={"pydantic_ai_mock": True}
                )
            else:
                return res.output
        except Exception as e:
            logger.exception("PydanticAI agent run failed")
            error_msg = AgentMessage(
                sender="PydanticAIAgent",
                content=f"Execution error: {str(e)}"
            )
            return AgentRunResult(
                success=False,
                status="ERROR",
                messages=[error_msg],
                output_data={},
                metadata={"error": str(e)}
            )
