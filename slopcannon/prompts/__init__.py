"""Prompt text, kept separate from agent logic.

Prompts are first-class and meant to be edited constantly as we learn what makes
the agents coordinate (or fail to). Each worker has a module here exposing three
constants — ROLE, OUTPUT_CONTRACT, TASK — that the Agent base class composes with
the shared collaboration rules.
"""
