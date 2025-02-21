from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import BaseLLM
from langchain_core.outputs import Generation, LLMResult


class LocalBaseLLM(BaseLLM):
    base_url: str = "http://localhost:11434"
    model_name: str = "deepseek-r1:7b"
    temperature: float = 0.7
    top_p: float = 0.9

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        generations = []

        for prompt in prompts:
            params = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": self.temperature,
                "top_p": self.top_p,
                **kwargs,
            }

            response = requests.post(f"{self.base_url}/api/generate", json=params)
            response.raise_for_status()

            result = response.json()
            generations.append([Generation(text=result["response"])])

        return LLMResult(generations=generations)

    @property
    def _llm_type(self) -> str:
        return "custom_ollama"
