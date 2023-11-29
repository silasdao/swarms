"""
Swarm Flow
Topic selection agent -> draft agent -> review agent -> distribution agent

Topic Selection Agent:
- Generate 10 topics on gaining mental clarity using Taosim and Christian meditation

Draft Agent:
- Write a 100% unique, creative and in human-like style article of a minimum of 5,000 words using headings and sub-headings.

Review Agent:
- Refine the article to meet PositiveMed’s stringent publication standards.

Distribution Agent:
- Social Media posts for the article.

# TODO
- Add shorter and better topic generator prompt
- Optimize writer prompt to create longer and more enjoyeable blogs
- Use Local Models like Storywriter
"""
from termcolor import colored
from swarms.models import OpenAIChat
from swarms.prompts.autoblogen import (
    DRAFT_AGENT_SYSTEM_PROMPT,
    REVIEW_PROMPT,
    SOCIAL_MEDIA_SYSTEM_PROMPT_AGENT,
    TOPIC_GENERATOR,
)
import os

api_key = os.environ["OPENAI_API_KEY"]
llm = OpenAIChat(openai_api_key=api_key)


def get_review_prompt(article):
    return REVIEW_PROMPT.replace("{{ARTICLE}}", article)


def social_media_prompt(article: str, goal: str = "Clicks and engagement"):
    return SOCIAL_MEDIA_SYSTEM_PROMPT_AGENT.replace(
        "{{ARTICLE}}", article
    ).replace("{{GOAL}}", goal)


# Agent that generates topics
topic_selection_task = (
    "Generate 10 topics on gaining mental clarity using ancient practices"
)
topics = llm(
    f"Your System Instructions: {TOPIC_GENERATOR}, Your current task: {topic_selection_task}"
)

dashboard = print(
    colored(
        f"""
    Topic Selection Agent
    -----------------------------

    Topics:
    ------------------------
    {topics}
    
    """,
        "blue",
    )
)


draft_blog = llm(DRAFT_AGENT_SYSTEM_PROMPT)
draft_out = print(
    colored(
        f"""
    
    ------------------------------------
    Drafter Writer Agent
    -----------------------------

    Draft:
    ------------------------
    {draft_blog}
    
    """,
        "red",
    )
)


# Agent that reviews the draft
review_agent = llm(get_review_prompt(draft_blog))
reviewed_draft = print(
    colored(
        f"""
    
    ------------------------------------
    Quality Assurance Writer Agent
    -----------------------------

    Complete Narrative:
    ------------------------
    {draft_blog}
    
    """,
        "blue",
    )
)


# Agent that publishes on social media
distribution_agent = llm(social_media_prompt(draft_blog, goal="Clicks and engagement"))
distribution_agent_out = print(
    colored(
        f"""
        --------------------------------
        Distribution Agent
        -------------------

        Social Media Posts
        -------------------
        {distribution_agent}

        """,
        "magenta",
    )
)
