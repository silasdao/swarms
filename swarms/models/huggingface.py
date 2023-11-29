import asyncio
import concurrent.futures
import logging
from typing import List, Tuple


import torch
from termcolor import colored
from torch.nn.parallel import DistributedDataParallel as DDP
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


class HuggingfaceLLM:
    """
    A class for running inference on a given model.

    Attributes:
        model_id (str): The ID of the model.
        device (str): The device to run the model on (either 'cuda' or 'cpu').
        max_length (int): The maximum length of the output sequence.
        quantize (bool, optional): Whether to use quantization. Defaults to False.
        quantization_config (dict, optional): The configuration for quantization.
        verbose (bool, optional): Whether to print verbose logs. Defaults to False.
        logger (logging.Logger, optional): The logger to use. Defaults to a basic logger.

    # Usage
    ```
    from swarms.models import HuggingfaceLLM

    model_id = "NousResearch/Yarn-Mistral-7b-128k"
    inference = HuggingfaceLLM(model_id=model_id)

    task = "Once upon a time"
    generated_text = inference(task)
    print(generated_text)
    ```
    """

    def __init__(
        self,
        model_id: str,
        device: str = None,
        max_length: int = 500,
        quantize: bool = False,
        quantization_config: dict = None,
        verbose=False,
        # logger=None,
        distributed=False,
        decoding=False,
        max_workers: int = 5,
        repitition_penalty: float = 1.3,
        no_repeat_ngram_size: int = 5,
        temperature: float = 0.7,
        top_k: int = 40,
        top_p: float = 0.8,
        *args,
        **kwargs,
    ):
        self.logger = logging.getLogger(__name__)
        self.device = (
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.model_id = model_id
        self.max_length = max_length
        self.verbose = verbose
        self.distributed = distributed
        self.decoding = decoding
        self.model, self.tokenizer = None, None
        self.quantize = quantize
        self.quantization_config = quantization_config
        self.max_workers = max_workers
        self.repitition_penalty = repitition_penalty
        self.no_repeat_ngram_size = no_repeat_ngram_size
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p

        if self.distributed:
            assert (
                torch.cuda.device_count() > 1
            ), "You need more than 1 gpu for distributed processing"

        bnb_config = None
        if quantize:
            if not quantization_config:
                quantization_config = {
                    "load_in_4bit": True,
                    "bnb_4bit_use_double_quant": True,
                    "bnb_4bit_quant_type": "nf4",
                    "bnb_4bit_compute_dtype": torch.bfloat16,
                }
            bnb_config = BitsAndBytesConfig(**quantization_config)

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id, *args, **kwargs
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, quantization_config=bnb_config, *args, **kwargs
            )

            self.model  # .to(self.device)
        except Exception as e:
            # self.logger.error(f"Failed to load the model or the tokenizer: {e}")
            # raise
            print(colored(f"Failed to load the model and or the tokenizer: {e}", "red"))

    def print_error(self, error: str):
        """Print error"""
        print(colored(f"Error: {error}", "red"))

    async def async_run(self, task: str):
        """Ashcnronous generate text for a given prompt"""
        return await asyncio.to_thread(self.run, task)

    def load_model(self):
        """Load the model"""
        if not self.model or not self.tokenizer:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)

                bnb_config = (
                    BitsAndBytesConfig(**self.quantization_config)
                    if self.quantization_config
                    else None
                )

                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_id, quantization_config=bnb_config
                ).to(self.device)

                if self.distributed:
                    self.model = DDP(self.model)
            except Exception as error:
                self.logger.error(f"Failed to load the model or the tokenizer: {error}")
                raise

    def concurrent_run(self, tasks: List[str], max_workers: int = 5):
        """Concurrently generate text for a list of prompts."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.run, tasks))
        return results

    def run_batch(self, tasks_images: List[Tuple[str, str]]) -> List[str]:
        """Process a batch of tasks and images"""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.run, task, img) for task, img in tasks_images
            ]
            results = [future.result() for future in futures]
        return results

    def run(self, task: str):
        """
        Generate a response based on the prompt text.

        Args:
        - task (str): Text to prompt the model.
        - max_length (int): Maximum length of the response.

        Returns:
        - Generated text (str).
        """
        self.load_model()

        max_length = self.max_length

        self.print_dashboard(task)

        try:
            inputs = self.tokenizer.encode(task, return_tensors="pt").to(self.device)

            # self.log.start()

            if self.decoding:
                with torch.no_grad():
                    for _ in range(max_length):
                        outputs = self.model.generate(
                            inputs, max_length=len(inputs) + 1, do_sample=True
                        )
                        output_tokens = outputs[0][-1]
                        output_sequence = [output_tokens.item()]
                        # print token in real-time
                        print(
                            self.tokenizer.decode(
                                [output_tokens], skip_special_tokens=True
                            ),
                            end="",
                            flush=True,
                        )
                        inputs = outputs
            else:
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs, max_length=max_length, do_sample=True
                    )

            del inputs
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            print(
                colored(
                    (
                        f"HuggingfaceLLM could not generate text because of error: {e},"
                        " try optimizing your arguments"
                    ),
                    "red",
                )
            )
            raise

    def __call__(self, task: str):
        """
        Generate a response based on the prompt text.

        Args:
        - task (str): Text to prompt the model.
        - max_length (int): Maximum length of the response.

        Returns:
        - Generated text (str).
        """
        self.load_model()

        max_length = self.max_length

        self.print_dashboard(task)

        try:
            inputs = self.tokenizer.encode(task, return_tensors="pt").to(self.device)

            # self.log.start()

            if self.decoding:
                with torch.no_grad():
                    for _ in range(max_length):
                        outputs = self.model.generate(
                            inputs, max_length=len(inputs) + 1, do_sample=True
                        )
                        output_tokens = outputs[0][-1]
                        output_sequence = [output_tokens.item()]
                        # print token in real-time
                        print(
                            self.tokenizer.decode(
                                [output_tokens], skip_special_tokens=True
                            ),
                            end="",
                            flush=True,
                        )
                        inputs = outputs
            else:
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs, max_length=max_length, do_sample=True
                    )

            del inputs

            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            self.logger.error(f"Failed to generate the text: {e}")
            raise

    async def __call_async__(self, task: str, *args, **kwargs) -> str:
        """Call the model asynchronously""" ""
        return await self.run_async(task, *args, **kwargs)

    def save_model(self, path: str):
        """Save the model to a given path"""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

    def gpu_available(self) -> bool:
        """Check if GPU is available"""
        return torch.cuda.is_available()

    def memory_consumption(self) -> dict:
        """Get the memory consumption of the GPU"""
        if not self.gpu_available():
            return {"error": "GPU not available"}
        torch.cuda.synchronize()
        allocated = torch.cuda.memory_allocated()
        reserved = torch.cuda.memory_reserved()
        return {"allocated": allocated, "reserved": reserved}

    def print_dashboard(self, task: str):
        """Print dashboard"""

        dashboard = print(
            colored(
                f"""
                HuggingfaceLLM Dashboard
                --------------------------------------------
                Model Name: {self.model_id}
                Tokenizer: {self.tokenizer}
                Model MaxLength: {self.max_length}
                Model Device: {self.device}
                Model Quantization: {self.quantize}
                Model Quantization Config: {self.quantization_config}
                Model Verbose: {self.verbose}
                Model Distributed: {self.distributed}
                Model Decoding: {self.decoding}

                ----------------------------------------
                Metadata:
                    Task Memory Consumption: {self.memory_consumption()}
                    GPU Available: {self.gpu_available()}
                ----------------------------------------

                Task Environment:
                    Task: {task}

                """,
                "red",
            )
        )

        print(dashboard)

    def set_device(self, device):
        """
        Changes the device used for inference.

        Parameters
        ----------
            device : str
                The new device to use for inference.
        """
        self.device = device
        self.model.to(self.device)

    def set_max_length(self, max_length):
        """Set max_length"""
        self.max_length = max_length

    def clear_chat_history(self):
        """Clear chat history"""
        self.chat_history = []
