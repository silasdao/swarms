import sys

log_file = open("errors.txt", "w")
sys.stderr = log_file

# LLMs
from swarms.models.anthropic import Anthropic  # noqa: E402
from swarms.models.petals import Petals  # noqa: E402
from swarms.models.mistral import Mistral  # noqa: E402
from swarms.models.openai_models import OpenAI, AzureOpenAI, OpenAIChat  # noqa: E402
from swarms.models.zephyr import Zephyr  # noqa: E402
from swarms.models.biogpt import BioGPT  # noqa: E402
from swarms.models.huggingface import HuggingfaceLLM  # noqa: E402
from swarms.models.wizard_storytelling import WizardLLMStoryTeller  # noqa: E402
from swarms.models.mpt import MPT7B  # noqa: E402

# MultiModal Models
from swarms.models.idefics import Idefics  # noqa: E402

# from swarms.models.kosmos_two import Kosmos  # noqa: E402
from swarms.models.vilt import Vilt  # noqa: E402
from swarms.models.nougat import Nougat  # noqa: E402
from swarms.models.layoutlm_document_qa import LayoutLMDocumentQA  # noqa: E402

# from swarms.models.gpt4v import GPT4Vision
# from swarms.models.dalle3 import Dalle3
# from swarms.models.distilled_whisperx import DistilWhisperModel # noqa: E402

__all__ = [
    "Anthropic",
    "Petals",
    "Mistral",
    "OpenAI",
    "AzureOpenAI",
    "OpenAIChat",
    "Zephyr",
    "Idefics",
    # "Kosmos",
    "Vilt",
    "Nougat",
    "LayoutLMDocumentQA",
    "BioGPT",
    "HuggingfaceLLM",
    "MPT7B",
    "WizardLLMStoryTeller",
    # "GPT4Vision",
    # "Dalle3",
]
