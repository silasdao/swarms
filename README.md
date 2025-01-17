![Swarming banner icon](images/swarmslogobanner.png)

<div align="center">

Swarms is a modular framework that enables reliable and useful multi-agent collaboration at scale to automate real-world tasks.


[![GitHub issues](https://img.shields.io/github/issues/kyegomez/swarms)](https://github.com/kyegomez/swarms/issues) [![GitHub forks](https://img.shields.io/github/forks/kyegomez/swarms)](https://github.com/kyegomez/swarms/network) [![GitHub stars](https://img.shields.io/github/stars/kyegomez/swarms)](https://github.com/kyegomez/swarms/stargazers) [![GitHub license](https://img.shields.io/github/license/kyegomez/swarms)](https://github.com/kyegomez/swarms/blob/main/LICENSE)[![GitHub star chart](https://img.shields.io/github/stars/kyegomez/swarms?style=social)](https://star-history.com/#kyegomez/swarms)[![Dependency Status](https://img.shields.io/librariesio/github/kyegomez/swarms)](https://libraries.io/github/kyegomez/swarms) [![Downloads](https://static.pepy.tech/badge/swarms/month)](https://pepy.tech/project/swarms)


### Share on Social Media

[![Join the Agora discord](https://img.shields.io/discord/1110910277110743103?label=Discord&logo=discord&logoColor=white&style=plastic&color=d7b023)![Share on Twitter](https://img.shields.io/twitter/url/https/twitter.com/cloudposse.svg?style=social&label=Share%20%40kyegomez/swarms)](https://twitter.com/intent/tweet?text=Check%20out%20this%20amazing%20AI%20project:%20&url=https%3A%2F%2Fgithub.com%2Fkyegomez%2Fswarms) [![Share on Facebook](https://img.shields.io/badge/Share-%20facebook-blue)](https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fgithub.com%2Fkyegomez%2Fswarms) [![Share on LinkedIn](https://img.shields.io/badge/Share-%20linkedin-blue)](https://www.linkedin.com/shareArticle?mini=true&url=https%3A%2F%2Fgithub.com%2Fkyegomez%2Fswarms&title=&summary=&source=)

[![Share on Reddit](https://img.shields.io/badge/-Share%20on%20Reddit-orange)](https://www.reddit.com/submit?url=https%3A%2F%2Fgithub.com%2Fkyegomez%2Fswarms&title=Swarms%20-%20the%20future%20of%20AI) [![Share on Hacker News](https://img.shields.io/badge/-Share%20on%20Hacker%20News-orange)](https://news.ycombinator.com/submitlink?u=https%3A%2F%2Fgithub.com%2Fkyegomez%2Fswarms&t=Swarms%20-%20the%20future%20of%20AI) [![Share on Pinterest](https://img.shields.io/badge/-Share%20on%20Pinterest-red)](https://pinterest.com/pin/create/button/?url=https%3A%2F%2Fgithub.com%2Fkyegomez%2Fswarms&media=https%3A%2F%2Fexample.com%2Fimage.jpg&description=Swarms%20-%20the%20future%20of%20AI) [![Share on WhatsApp](https://img.shields.io/badge/-Share%20on%20WhatsApp-green)](https://api.whatsapp.com/send?text=Check%20out%20Swarms%20-%20the%20future%20of%20AI%20%23swarms%20%23AI%0A%0Ahttps%3A%2F%2Fgithub.com%2Fkyegomez%2Fswarms)

</div>

<!-- [![Swarm Fest](images/swarmfest.png)](https://github.com/users/kyegomez/projects/1) -->

## Vision
At Swarms, we're transforming the landscape of AI from siloed AI agents to a unified 'swarm' of intelligence. Through relentless iteration and the power of collective insight from our 1500+ Agora researchers, we're developing a groundbreaking framework for AI collaboration. Our mission is to catalyze a paradigm shift, advancing Humanity with the power of unified autonomous AI agent swarms.

-----

## 🤝 Schedule a 1-on-1 Session

Book a [1-on-1 Session with Kye](https://calendly.com/swarm-corp/30min), the Creator, to discuss any issues, provide feedback, or explore how we can improve Swarms for you.


----------

## Installation
`pip3 install --upgrade swarms`

---

## Usage
We have a small gallery of examples to run here, [for more check out the docs to build your own agent and or swarms!](https://docs.apac.ai)

### Example in Colab:

<a target="_blank" href="https://colab.research.google.com/github/kyegomez/swarms/blob/master/swarms_example.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a> Run example in Colab, using your OpenAI API key. 

### `Flow` Example
- Reliable Structure that provides LLMS autonomy
- Extremely Customizeable with stopping conditions, interactivity, dynamical temperature, loop intervals, and so much more
- Enterprise Grade + Production Grade: `Flow` is designed and optimized for automating real-world tasks at scale!

```python

from swarms.models import OpenAIChat
from swarms.structs import Flow

api_key = ""

# Initialize the language model, this model can be swapped out with Anthropic, ETC, Huggingface Models like Mistral, ETC
llm = OpenAIChat(
    # model_name="gpt-4"
    openai_api_key=api_key,
    temperature=0.5,
    # max_tokens=100,
)

## Initialize the workflow
flow = Flow(
    llm=llm,
    max_loops=2,
    dashboard=True,
    # stopping_condition=None,  # You can define a stopping condition as needed.
    # loop_interval=1,
    # retry_attempts=3,
    # retry_interval=1,
    # interactive=False,  # Set to 'True' for interactive mode.
    # dynamic_temperature=False,  # Set to 'True' for dynamic temperature handling.
)

# out = flow.load_state("flow_state.json")
# temp = flow.dynamic_temperature()
# filter = flow.add_response_filter("Trump")
out = flow.run("Generate a 10,000 word blog on health and wellness.")
# out = flow.validate_response(out)
# out = flow.analyze_feedback(out)
# out = flow.print_history_and_memory()
# # out = flow.save_state("flow_state.json")
# print(out)



```

------

### `SequentialWorkflow`
- A Sequential swarm of autonomous agents where each agent's outputs are fed into the next agent
- Save and Restore Workflow states!
- Integrate Flow's with various LLMs and Multi-Modality Models

```python
from swarms.models import OpenAIChat, BioGPT, Anthropic
from swarms.structs import Flow
from swarms.structs.sequential_workflow import SequentialWorkflow


# Example usage
api_key = (
    ""  # Your actual API key here
)

# Initialize the language flow
llm = OpenAIChat(
    openai_api_key=api_key,
    temperature=0.5,
    max_tokens=3000,
)

biochat = BioGPT()

# Use Anthropic
anthropic = Anthropic()

# Initialize the agent with the language flow
agent1 = Flow(llm=llm, max_loops=1, dashboard=False)

# Create another agent for a different task
agent2 = Flow(llm=llm, max_loops=1, dashboard=False)

# Create another agent for a different task
agent3 = Flow(llm=biochat, max_loops=1, dashboard=False)

# agent4 = Flow(llm=anthropic, max_loops="auto")

# Create the workflow
workflow = SequentialWorkflow(max_loops=1)

# Add tasks to the workflow
workflow.add("Generate a 10,000 word blog on health and wellness.", agent1)

# Suppose the next task takes the output of the first task as input
workflow.add("Summarize the generated blog", agent2)

workflow.add("Create a references sheet of materials for the curriculm", agent3)

# Run the workflow
workflow.run()

# Output the results
for task in workflow.tasks:
    print(f"Task: {task.description}, Result: {task.result}")

```

---

# Features 🤖 
The Swarms framework is designed with a strong emphasis on reliability, performance, and production-grade readiness. 
Below are the key features that make Swarms an ideal choice for enterprise-level AI deployments.

## 🚀 Production-Grade Readiness
- **Scalable Architecture**: Built to scale effortlessly with your growing business needs.
- **Enterprise-Level Security**: Incorporates top-notch security features to safeguard your data and operations.
- **Containerization and Microservices**: Easily deployable in containerized environments, supporting microservices architecture.

## ⚙️ Reliability and Robustness
- **Fault Tolerance**: Designed to handle failures gracefully, ensuring uninterrupted operations.
- **Consistent Performance**: Maintains high performance even under heavy loads or complex computational demands.
- **Automated Backup and Recovery**: Features automatic backup and recovery processes, reducing the risk of data loss.

## 💡 Advanced AI Capabilities

The Swarms framework is equipped with a suite of advanced AI capabilities designed to cater to a wide range of applications and scenarios, ensuring versatility and cutting-edge performance.

### Multi-Modal Autonomous Agents
- **Versatile Model Support**: Seamlessly works with various AI models, including NLP, computer vision, and more, for comprehensive multi-modal capabilities.
- **Context-Aware Processing**: Employs context-aware processing techniques to ensure relevant and accurate responses from agents.

### Function Calling Models for API Execution
- **Automated API Interactions**: Function calling models that can autonomously execute API calls, enabling seamless integration with external services and data sources.
- **Dynamic Response Handling**: Capable of processing and adapting to responses from APIs for real-time decision making.

### Varied Architectures of Swarms
- **Flexible Configuration**: Supports multiple swarm architectures, from centralized to decentralized, for diverse application needs.
- **Customizable Agent Roles**: Allows customization of agent roles and behaviors within the swarm to optimize performance and efficiency.

### Generative Models
- **Advanced Generative Capabilities**: Incorporates state-of-the-art generative models to create content, simulate scenarios, or predict outcomes.
- **Creative Problem Solving**: Utilizes generative AI for innovative problem-solving approaches and idea generation.

### Enhanced Decision-Making
- **AI-Powered Decision Algorithms**: Employs advanced algorithms for swift and effective decision-making in complex scenarios.
- **Risk Assessment and Management**: Capable of assessing risks and managing uncertain situations with AI-driven insights.

### Real-Time Adaptation and Learning
- **Continuous Learning**: Agents can continuously learn and adapt from new data, improving their performance and accuracy over time.
- **Environment Adaptability**: Designed to adapt to different operational environments, enhancing robustness and reliability.


## 🔄 Efficient Workflow Automation
- **Streamlined Task Management**: Simplifies complex tasks with automated workflows, reducing manual intervention.
- **Customizable Workflows**: Offers customizable workflow options to fit specific business needs and requirements.
- **Real-Time Analytics and Reporting**: Provides real-time insights into agent performance and system health.

## 🌐 Wide-Ranging Integration
- **API-First Design**: Easily integrates with existing systems and third-party applications via robust APIs.
- **Cloud Compatibility**: Fully compatible with major cloud platforms for flexible deployment options.
- **Continuous Integration/Continuous Deployment (CI/CD)**: Supports CI/CD practices for seamless updates and deployment.

## 📊 Performance Optimization
- **Resource Management**: Efficiently manages computational resources for optimal performance.
- **Load Balancing**: Automatically balances workloads to maintain system stability and responsiveness.
- **Performance Monitoring Tools**: Includes comprehensive monitoring tools for tracking and optimizing performance.

## 🛡️ Security and Compliance
- **Data Encryption**: Implements end-to-end encryption for data at rest and in transit.
- **Compliance Standards Adherence**: Adheres to major compliance standards ensuring legal and ethical usage.
- **Regular Security Updates**: Regular updates to address emerging security threats and vulnerabilities.

## 💬 Community and Support
- **Extensive Documentation**: Detailed documentation for easy implementation and troubleshooting.
- **Active Developer Community**: A vibrant community for sharing ideas, solutions, and best practices.
- **Professional Support**: Access to professional support for enterprise-level assistance and guidance.

Swarms framework is not just a tool but a robust, scalable, and secure partner in your AI journey, ready to tackle the challenges of modern AI applications in a business environment.


## Documentation
- For documentation, go here, [swarms.apac.ai](https://swarms.apac.ai)


## Contribute
- We're always looking for contributors to help us improve and expand this project. If you're interested, please check out our [Contributing Guidelines](CONTRIBUTING.md) and our [contributing board](https://github.com/users/kyegomez/projects/1)

## Community
- [Join the Swarms community here on Discord!](https://discord.gg/AJazBmhKnr)

# Discovery Call
Book a discovery call with the Swarms team to learn how to optimize and scale your swarm! [Click here to book a time that works for you!](https://calendly.com/swarm-corp/30min?month=2023-11)

# License
MIT
