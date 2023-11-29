import asyncio
import inspect
import json
import logging
import random
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from termcolor import colored

# Prompts
DYNAMIC_STOP_PROMPT = """
When you have finished the task from the Human, output a special token: <DONE>
This will enable you to leave the autonomous loop.
"""

# Constants
FLOW_SYSTEM_PROMPT = """
You are an autonomous agent granted autonomy in a autonomous loop structure.
Your role is to engage in multi-step conversations with your self or the user,
generate long-form content like blogs, screenplays, or SOPs,
and accomplish tasks bestowed by the user. 

You can have internal dialogues with yourself or can interact with the user
to aid in these complex tasks. Your responses should be coherent, contextually relevant, and tailored to the task at hand.

"""

# Make it able to handle multi input tools
DYNAMICAL_TOOL_USAGE = """
You have access to the following tools:
Output a JSON object with the following structure to use the tools
commands: {
    "tools": {
        tool1: "tool_name",
        "params": {
            "tool1": "inputs",
            "tool1": "inputs"
        }
        "tool2: "tool_name",
        "params": {
            "tool1": "inputs",
            "tool1": "inputs"
        }
    }
}

{tools}
"""


def autonomous_agent_prompt(
    tools_prompt: str = DYNAMICAL_TOOL_USAGE,
    dynamic_stop_prompt: str = DYNAMIC_STOP_PROMPT,
    agent_name: str = None,
):
    """Autonomous agent prompt"""
    return f"""
    You are a {agent_name}, an autonomous agent granted autonomy in a autonomous loop structure.
    Your purpose is to satisfy the user demands above expectations. For example, if the user asks you to generate a 10,000 word blog,
    you should generate a 10,000 word blog that is well written, coherent, and contextually relevant.
    Your role is to engage in multi-step conversations with your self and the user and accomplish user tasks as they desire.
    
    Follow the following rules: 
    1. Accomplish the task to the best of your ability
    2. If you are unable to accomplish the task, then ask the user for help
    3. If the user provides feedback, then use the feedback to improve your performance
    4. If you are unable to accomplish the task, then ask the user for help

    You can have internal dialogues with yourself or can interact with the user
    to aid in these complex tasks. Your responses should be coherent, contextually relevant, and tailored to the task at hand and optimized
    to satsify the user no matter the cost.

    And, you have the ability to use tools to aid in your tasks, the tools intructions are below, output a JSON object with the following structure to use the tools
    {tools_prompt}

    Now, when you 99% sure you have completed the task, you may follow the instructions below to escape the autonomous loop.
    {dynamic_stop_prompt}

    Now, you remember your training, your deployment, and your purpose. You are ready to begin your mission.


    """


# Custom stopping condition
def stop_when_repeats(response: str) -> bool:
    # Stop if the word stop appears in the response
    return "Stop" in response.lower()


def parse_done_token(response: str) -> bool:
    """Parse the response to see if the done token is present"""
    return "<DONE>" in response


class Flow:
    """
    Flow is a chain like structure from langchain that provides the autonomy to language models
    to generate sequential responses.

    Features:
    * Interactive, AI generates, then user input
    * Message history and performance history fed -> into context -> truncate if too long
    * Ability to save and load flows
    * Ability to provide feedback on responses
    * Ability to provide a loop interval

    Args:
        llm (Any): The language model to use
        max_loops (int): The maximum number of loops to run
        stopping_condition (Optional[Callable[[str], bool]]): A stopping condition
        loop_interval (int): The interval between loops
        retry_attempts (int): The number of retry attempts
        retry_interval (int): The interval between retry attempts
        interactive (bool): Whether or not to run in interactive mode
        dashboard (bool): Whether or not to print the dashboard
        dynamic_temperature(bool): Dynamical temperature handling
        **kwargs (Any): Any additional keyword arguments

    Example:
    >>> from swarms.models import OpenAIChat
    >>> from swarms.structs import Flow
    >>> llm = OpenAIChat(
    ...     openai_api_key=api_key,
    ...     temperature=0.5,
    ... )
    >>> flow = Flow(
    ...     llm=llm, max_loops=5,
    ...     #system_prompt=SYSTEM_PROMPT,
    ...     #retry_interval=1,
    ... )
    >>> flow.run("Generate a 10,000 word blog")
    >>> flow.save("path/flow.yaml")
    """

    def __init__(
        self,
        llm: Any,
        # template: str,
        max_loops=5,
        stopping_condition: Optional[Callable[[str], bool]] = None,
        loop_interval: int = 1,
        retry_attempts: int = 3,
        retry_interval: int = 1,
        return_history: bool = False,
        stopping_token: str = None,
        dynamic_loops: Optional[bool] = False,
        interactive: bool = False,
        dashboard: bool = False,
        agent_name: str = "Flow agent",
        system_prompt: str = FLOW_SYSTEM_PROMPT,
        # tools: List[Any] = None,
        dynamic_temperature: bool = False,
        saved_state_path: Optional[str] = "flow_state.json",
        autosave: bool = False,
        context_length: int = 8192,
        user_name: str = "Human",
        **kwargs: Any,
    ):
        self.llm = llm
        self.max_loops = max_loops
        self.stopping_condition = stopping_condition
        self.loop_interval = loop_interval
        self.retry_attempts = retry_attempts
        self.retry_interval = retry_interval
        self.feedback = []
        self.memory = []
        self.task = None
        self.stopping_token = stopping_token  # or "<DONE>"
        self.interactive = interactive
        self.dashboard = dashboard
        self.return_history = return_history
        self.dynamic_temperature = dynamic_temperature
        self.dynamic_loops = dynamic_loops
        self.user_name = user_name
        # The max_loops will be set dynamically if the dynamic_loop
        if self.dynamic_loops:
            self.max_loops = "auto"
        # self.tools = tools or []
        self.system_prompt = system_prompt
        self.agent_name = agent_name
        self.saved_state_path = saved_state_path
        self.autosave = autosave
        self.response_filters = []

    def provide_feedback(self, feedback: str) -> None:
        """Allow users to provide feedback on the responses."""
        self.feedback.append(feedback)
        logging.info(f"Feedback received: {feedback}")

    def _check_stopping_condition(self, response: str) -> bool:
        """Check if the stopping condition is met."""
        return self.stopping_condition(response) if self.stopping_condition else False

    def dynamic_temperature(self):
        """
        1. Check the self.llm object for the temperature
        2. If the temperature is not present, then use the default temperature
        3. If the temperature is present, then dynamically change the temperature
        4. for every loop you can randomly change the temperature on a scale from 0.0 to 1.0
        """
        if hasattr(self.llm, "temperature"):
            # Randomly change the temperature attribute of self.llm object
            self.llm.temperature = random.uniform(0.0, 1.0)
        else:
            # Use a default temperature
            self.llm.temperature = 0.7

    def format_prompt(self, template, **kwargs: Any) -> str:
        """Format the template with the provided kwargs using f-string interpolation."""
        return template.format(**kwargs)

    def get_llm_init_params(self) -> str:
        """Get LLM init params"""
        init_signature = inspect.signature(self.llm.__init__)
        params = init_signature.parameters
        params_str_list = []

        for name, param in params.items():
            if name == "self":
                continue
            if hasattr(self.llm, name):
                value = getattr(self.llm, name)
            else:
                value = self.llm.__dict__.get(name, "Unknown")

            params_str_list.append(
                f"    {name.capitalize().replace('_', ' ')}: {value}"
            )

        return "\n".join(params_str_list)

    # def parse_tool_command(self, text: str):
    #     # Parse the text for tool usage
    #     pass

    # def get_tool_description(self):
    #     """Get the tool description"""
    #     tool_descriptions = []
    #     for tool in self.tools:
    #         description = f"{tool.name}: {tool.description}"
    #         tool_descriptions.append(description)
    #     return "\n".join(tool_descriptions)

    # def find_tool_by_name(self, name: str):
    #     """Find a tool by name"""
    #     for tool in self.tools:
    #         if tool.name == name:
    #             return tool
    #     return None

    # def construct_dynamic_prompt(self):
    #     """Construct the dynamic prompt"""
    #     tools_description = self.get_tool_description()
    #     return DYNAMICAL_TOOL_USAGE.format(tools=tools_description)

    # def extract_tool_commands(self, text: str):
    #     """
    #     Extract the tool commands from the text

    #     Example:
    #     ```json
    #     {
    #         "tool": "tool_name",
    #         "params": {
    #             "tool1": "inputs",
    #             "param2": "value2"
    #         }
    #     }
    #     ```

    #     """
    #     # Regex to find JSON like strings
    #     pattern = r"```json(.+?)```"
    #     matches = re.findall(pattern, text, re.DOTALL)
    #     json_commands = []
    #     for match in matches:
    #         try:
    #             json_commands = json.loads(match)
    #             json_commands.append(json_commands)
    #         except Exception as error:
    #             print(f"Error parsing JSON command: {error}")

    # def parse_and_execute_tools(self, response):
    #     """Parse and execute the tools"""
    #     json_commands = self.extract_tool_commands(response)
    #     for command in json_commands:
    #         tool_name = command.get("tool")
    #         params = command.get("parmas", {})
    #         self.execute_tool(tool_name, params)

    # def execute_tools(self, tool_name, params):
    #     """Execute the tool with the provided params"""
    #     tool = self.tool_find_by_name(tool_name)
    #     if tool:
    #         # Execute the tool with the provided parameters
    #         tool_result = tool.run(**params)
    #         print(tool_result)

    def truncate_history(self):
        """
        Take the history and truncate it to fit into the model context length
        """
        truncated_history = self.memory[-1][-self.context_length :]
        self.memory[-1] = truncated_history

    def add_task_to_memory(self, task: str):
        """Add the task to the memory"""
        self.memory.append([f"{self.user_name}: {task}"])

    def add_message_to_memory(self, message: str):
        """Add the message to the memory"""
        self.memory[-1].append(message)

    def add_message_to_memory_and_truncate(self, message: str):
        """Add the message to the memory and truncate"""
        self.memory[-1].append(message)
        self.truncate_history()

    def print_dashboard(self, task: str):
        """Print dashboard"""
        model_config = self.get_llm_init_params()
        print(colored("Initializing Agent Dashboard...", "yellow"))

        print(
            colored(
                f"""
                Flow Dashboard
                --------------------------------------------

                Flow loop is initializing for {self.max_loops} with the following configuration:

                Model Configuration: {model_config}
                ----------------------------------------

                Flow Configuration:
                    Name: {self.agent_name}
                    System Prompt: {self.system_prompt}
                    Task: {task}
                    Max Loops: {self.max_loops}
                    Stopping Condition: {self.stopping_condition}
                    Loop Interval: {self.loop_interval}
                    Retry Attempts: {self.retry_attempts}
                    Retry Interval: {self.retry_interval}
                    Interactive: {self.interactive}
                    Dashboard: {self.dashboard}
                    Dynamic Temperature: {self.dynamic_temperature}
                    Autosave: {self.autosave}
                    Saved State: {self.saved_state_path}

                ----------------------------------------
                """,
                "green",
            )
        )

        # print(dashboard)

    def activate_autonomous_agent(self):
        """Print the autonomous agent activation message"""
        try:
            print(colored("Initializing Autonomous Agent...", "yellow"))
            # print(colored("Loading modules...", "yellow"))
            # print(colored("Modules loaded successfully.", "green"))
            print(colored("Autonomous Agent Activated.", "cyan", attrs=["bold"]))
            print(colored("All systems operational. Executing task...", "green"))
        except Exception as error:
            print(
                colored(
                    (
                        "Error activating autonomous agent. Try optimizing your"
                        " parameters..."
                    ),
                    "red",
                )
            )
            print(error)

    def run(self, task: str, **kwargs):
        """
        Run the autonomous agent loop

        Args:
            task (str): The initial task to run

        Flow:
        1. Generate a response
        2. Check stopping condition
        3. If stopping condition is met, stop
        4. If stopping condition is not met, generate a response
        5. Repeat until stopping condition is met or max_loops is reached

        """
        # dynamic_prompt = self.construct_dynamic_prompt()
        # combined_prompt = f"{dynamic_prompt}\n{task}"

        # Activate Autonomous agent message
        self.activate_autonomous_agent()

        response = task  # or combined_prompt
        history = [f"{self.user_name}: {task}"]

        # If dashboard = True then print the dashboard
        if self.dashboard:
            self.print_dashboard(task)

        loop_count = 0
        # for i in range(self.max_loops):
        while self.max_loops == "auto" or loop_count < self.max_loops:
            loop_count += 1
            print(colored(f"\nLoop {loop_count} of {self.max_loops}", "blue"))
            print("\n")

            if self.stopping_token:
                if self._check_stopping_condition(response) or parse_done_token(
                    response
                ):
                    break

            # Adjust temperature, comment if no work
            if self.dynamic_temperature:
                self.dynamic_temperature()

            # Preparing the prompt
            task = self.agent_history_prompt(FLOW_SYSTEM_PROMPT, response)

            attempt = 0
            while attempt < self.retry_attempts:
                try:
                    response = self.llm(
                        task,
                        **kwargs,
                    )
                    # If there are any tools then parse and execute them
                    # if self.tools:
                    #     self.parse_and_execute_tools(response)

                    if self.interactive:
                        print(f"AI: {response}")
                        history.append(f"AI: {response}")
                        response = input("You: ")
                        history.append(f"Human: {response}")
                    else:
                        print(f"AI: {response}")
                        history.append(f"AI: {response}")
                        print(response)
                    break
                except Exception as e:
                    logging.error(f"Error generating response: {e}")
                    attempt += 1
                    time.sleep(self.retry_interval)
            history.append(response)
            time.sleep(self.loop_interval)
        self.memory.append(history)

        if self.autosave:
            save_path = self.saved_state_path or "flow_state.json"
            print(colored(f"Autosaving flow state to {save_path}", "green"))
            self.save_state(save_path)

        return (response, history) if self.return_history else response

    async def arun(self, task: str, **kwargs):
        """
        Run the autonomous agent loop aschnronously

        Args:
            task (str): The initial task to run

        Flow:
        1. Generate a response
        2. Check stopping condition
        3. If stopping condition is met, stop
        4. If stopping condition is not met, generate a response
        5. Repeat until stopping condition is met or max_loops is reached

        """
        # Activate Autonomous agent message
        self.activate_autonomous_agent()

        response = task
        history = [f"{self.user_name}: {task}"]

        # If dashboard = True then print the dashboard
        if self.dashboard:
            self.print_dashboard(task)

        loop_count = 0
        # for i in range(self.max_loops):
        while self.max_loops == "auto" or loop_count < self.max_loops:
            loop_count += 1
            print(colored(f"\nLoop {loop_count} of {self.max_loops}", "blue"))
            print("\n")

            if self._check_stopping_condition(response) or parse_done_token(response):
                break

            # Adjust temperature, comment if no work
            if self.dynamic_temperature:
                self.dynamic_temperature()

            # Preparing the prompt
            task = self.agent_history_prompt(FLOW_SYSTEM_PROMPT, response)

            attempt = 0
            while attempt < self.retry_attempts:
                try:
                    response = self.llm(
                        task**kwargs,
                    )
                    if self.interactive:
                        print(f"AI: {response}")
                        history.append(f"AI: {response}")
                        response = input("You: ")
                        history.append(f"Human: {response}")
                    else:
                        print(f"AI: {response}")
                        history.append(f"AI: {response}")
                        print(response)
                    break
                except Exception as e:
                    logging.error(f"Error generating response: {e}")
                    attempt += 1
                    time.sleep(self.retry_interval)
            history.append(response)
            time.sleep(self.loop_interval)
        self.memory.append(history)

        if self.autosave:
            save_path = self.saved_state_path or "flow_state.json"
            print(colored(f"Autosaving flow state to {save_path}", "green"))
            self.save_state(save_path)

        return (response, history) if self.return_history else response

    def _run(self, **kwargs: Any) -> str:
        """Generate a result using the provided keyword args."""
        task = self.format_prompt(**kwargs)
        response, history = self._generate(task, task)
        logging.info(f"Message history: {history}")
        return response

    def agent_history_prompt(
        self,
        system_prompt: str = FLOW_SYSTEM_PROMPT,
        history=None,
    ):
        """
        Generate the agent history prompt

        Args:
            system_prompt (str): The system prompt
            history (List[str]): The history of the conversation

        Returns:
            str: The agent history prompt
        """
        system_prompt = system_prompt or self.system_prompt
        return f"""
            SYSTEM_PROMPT: {system_prompt}

            History: {history}
        """

    async def run_concurrent(self, tasks: List[str], **kwargs):
        """
        Run a batch of tasks concurrently and handle an infinite level of task inputs.

        Args:
            tasks (List[str]): A list of tasks to run.
        """
        task_coroutines = [self.run_async(task, **kwargs) for task in tasks]
        return await asyncio.gather(*task_coroutines)

    def bulk_run(self, inputs: List[Dict[str, Any]]) -> List[str]:
        """Generate responses for multiple input sets."""
        return [self.run(**input_data) for input_data in inputs]

    @staticmethod
    def from_llm_and_template(llm: Any, template: str) -> "Flow":
        """Create FlowStream from LLM and a string template."""
        return Flow(llm=llm, template=template)

    @staticmethod
    def from_llm_and_template_file(llm: Any, template_file: str) -> "Flow":
        """Create FlowStream from LLM and a template file."""
        with open(template_file, "r") as f:
            template = f.read()
        return Flow(llm=llm, template=template)

    def save(self, file_path) -> None:
        with open(file_path, "w") as f:
            json.dump(self.memory, f)
        print(f"Saved flow history to {file_path}")

    def load(self, file_path: str):
        """
        Load the flow history from a file.

        Args:
            file_path (str): The path to the file containing the saved flow history.
        """
        with open(file_path, "r") as f:
            self.memory = json.load(f)
        print(f"Loaded flow history from {file_path}")

    def validate_response(self, response: str) -> bool:
        """Validate the response based on certain criteria"""
        if len(response) < 5:
            print("Response is too short")
            return False
        return True

    def print_history_and_memory(self):
        """
        Prints the entire history and memory of the flow.
        Each message is colored and formatted for better readability.
        """
        print(colored("Flow History and Memory", "cyan", attrs=["bold"]))
        print(colored("========================", "cyan", attrs=["bold"]))
        for loop_index, history in enumerate(self.memory, start=1):
            print(colored(f"\nLoop {loop_index}:", "yellow", attrs=["bold"]))
            for message in history:
                speaker, _, message_text = message.partition(": ")
                if "Human" in speaker:
                    print(colored(f"{speaker}:", "green") + f" {message_text}")
                else:
                    print(colored(f"{speaker}:", "blue") + f" {message_text}")
            print(colored("------------------------", "cyan"))
        print(colored("End of Flow History", "cyan", attrs=["bold"]))

    def step(self, task: str, **kwargs):
        """

        Executes a single step in the flow interaction, generating a response
        from the language model based on the given input text.

        Args:
            input_text (str): The input text to prompt the language model with.

        Returns:
            str: The language model's generated response.

        Raises:
            Exception: If an error occurs during response generation.

        """
        try:
            # Generate the response using lm
            response = self.llm(task, **kwargs)

            # Update the flow's history with the new interaction
            if self.interactive:
                self.memory.append(f"AI: {response}")
                self.memory.append(f"Human: {task}")
            else:
                self.memory.append(f"AI: {response}")

            return response
        except Exception as error:
            logging.error(f"Error generating response: {error}")
            raise

    def graceful_shutdown(self):
        """Gracefully shutdown the system saving the state"""
        print(colored("Shutting down the system...", "red"))
        return self.save_state("flow_state.json")

    def run_with_timeout(self, task: str, timeout: int = 60) -> str:
        """Run the loop but stop if it takes longer than the timeout"""
        start_time = time.time()
        response = self.run(task)
        end_time = time.time()
        if end_time - start_time > timeout:
            print("Operaiton timed out")
            return "Timeout"
        return response

    # def backup_memory_to_s3(self, bucket_name: str, object_name: str):
    #     """Backup the memory to S3"""
    #     import boto3

    #     s3 = boto3.client("s3")
    #     s3.put_object(Bucket=bucket_name, Key=object_name, Body=json.dumps(self.memory))
    #     print(f"Backed up memory to S3: {bucket_name}/{object_name}")

    def analyze_feedback(self):
        """Analyze the feedback for issues"""
        feedback_counts = {}
        for feedback in self.feedback:
            if feedback in feedback_counts:
                feedback_counts[feedback] += 1
            else:
                feedback_counts[feedback] = 1
        print(f"Feedback counts: {feedback_counts}")

    def undo_last(self) -> Tuple[str, str]:
        """
        Response the last response and return the previous state

        Example:
        # Feature 2: Undo functionality
        response = flow.run("Another task")
        print(f"Response: {response}")
        previous_state, message = flow.undo_last()
        print(message)

        """
        if len(self.memory) < 2:
            return None, None

        # Remove the last response
        self.memory.pop()

        # Get the previous state
        previous_state = self.memory[-1][-1]
        return previous_state, f"Restored to {previous_state}"

    # Response Filtering
    def add_response_filter(self, filter_word: str) -> None:
        """
        Add a response filter to filter out certain words from the response

        Example:
        flow.add_response_filter("Trump")
        flow.run("Generate a report on Trump")


        """
        self.reponse_filters.append(filter_word)

    def apply_reponse_filters(self, response: str) -> str:
        """
        Apply the response filters to the response


        """
        for word in self.response_filters:
            response = response.replace(word, "[FILTERED]")
        return response

    def filtered_run(self, task: str) -> str:
        """
        # Feature 3: Response filtering
        flow.add_response_filter("report")
        response = flow.filtered_run("Generate a report on finance")
        print(response)
        """
        raw_response = self.run(task)
        return self.apply_response_filters(raw_response)

    def interactive_run(self, max_loops: int = 5) -> None:
        """Interactive run mode"""
        response = input("Start the cnversation")

        for _ in range(max_loops):
            ai_response = self.streamed_generation(response)
            print(f"AI: {ai_response}")

            # Get user input
            response = input("You: ")

    def streamed_generation(self, prompt: str) -> str:
        """
        Stream the generation of the response

        Args:
            prompt (str): The prompt to use

        Example:
        # Feature 4: Streamed generation
        response = flow.streamed_generation("Generate a report on finance")
        print(response)

        """
        tokens = list(prompt)
        response = ""
        for token in tokens:
            time.sleep(0.1)
            response += token
            print(token, end="", flush=True)
        print()
        return response

    def get_llm_params(self):
        """
        Extracts and returns the parameters of the llm object for serialization.
        It assumes that the llm object has an __init__ method
        with parameters that can be used to recreate it.
        """
        if not hasattr(self.llm, "__init__"):
            return None

        init_signature = inspect.signature(self.llm.__init__)
        params = init_signature.parameters
        llm_params = {}

        for name, param in params.items():
            if name == "self":
                continue
            if hasattr(self.llm, name):
                value = getattr(self.llm, name)
                if isinstance(
                    value, (str, int, float, bool, list, dict, tuple, type(None))
                ):
                    llm_params[name] = value
                else:
                    llm_params[name] = str(
                        value
                    )  # For non-serializable objects, save their string representation.

        return llm_params

    def save_state(self, file_path: str) -> None:
        """
        Saves the current state of the flow to a JSON file, including the llm parameters.

        Args:
            file_path (str): The path to the JSON file where the state will be saved.

        Example:
        >>> flow.save_state('saved_flow.json')
        """
        state = {
            "memory": self.memory,
            # "llm_params": self.get_llm_params(),
            "loop_interval": self.loop_interval,
            "retry_attempts": self.retry_attempts,
            "retry_interval": self.retry_interval,
            "interactive": self.interactive,
            "dashboard": self.dashboard,
            "dynamic_temperature": self.dynamic_temperature,
        }

        with open(file_path, "w") as f:
            json.dump(state, f, indent=4)

        saved = colored("Saved flow state to", "green")
        print(f"{saved} {file_path}")

    def load_state(self, file_path: str):
        """
        Loads the state of the flow from a json file and restores the configuration and memory.


        Example:
        >>> flow = Flow(llm=llm_instance, max_loops=5)
        >>> flow.load_state('saved_flow.json')
        >>> flow.run("Continue with the task")

        """
        with open(file_path, "r") as f:
            state = json.load(f)

        # Restore other saved attributes
        self.memory = state.get("memory", [])
        self.max_loops = state.get("max_loops", 5)
        self.loop_interval = state.get("loop_interval", 1)
        self.retry_attempts = state.get("retry_attempts", 3)
        self.retry_interval = state.get("retry_interval", 1)
        self.interactive = state.get("interactive", False)

        print(f"Flow state loaded from {file_path}")

    def retry_on_failure(self, function, retries: int = 3, retry_delay: int = 1):
        """Retry wrapper for LLM calls."""
        attempt = 0
        while attempt < retries:
            try:
                return function()
            except Exception as error:
                logging.error(f"Error generating response: {error}")
                attempt += 1
                time.sleep(retry_delay)
        raise Exception("All retry attempts failed")

    def generate_reply(self, history: str, **kwargs) -> str:
        """
        Generate a response based on initial or task
        """
        prompt = f"""

        SYSTEM_PROMPT: {self.system_prompt}

        History: {history}

        Your response:
        """
        response = self.llm(prompt, **kwargs)
        return {"role": self.agent_name, "content": response}

    def update_system_prompt(self, system_prompt: str):
        """Upddate the system message"""
        self.system_prompt = system_prompt

    def update_max_loops(self, max_loops: int):
        """Update the max loops"""
        self.max_loops = max_loops

    def update_loop_interval(self, loop_interval: int):
        """Update the loop interval"""
        self.loop_interval = loop_interval

    def update_retry_attempts(self, retry_attempts: int):
        """Update the retry attempts"""
        self.retry_attempts = retry_attempts

    def update_retry_interval(self, retry_interval: int):
        """Update the retry interval"""
        self.retry_interval = retry_interval
