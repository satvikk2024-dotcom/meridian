"""
Planner: decides which agents to run for a given company.

For MVP, we always run all four agents. The planner exists as a separate
module so Phase 9 (evaluation) can swap in subsets of agents without
touching the runner, and so interviewers can see you thought about
extensibility without over-engineering it.
"""
from app.agents.base import Agent
from app.agents.financial import FinancialAgent
from app.agents.market import MarketAgent
from app.agents.people import PeopleAgent
from app.agents.customer import CustomerSentimentAgent


def agents_for(company: str, ticker: str) -> list[Agent]:
    """Return the agents that should run for this company/ticker pair."""
    return [
        FinancialAgent(),
        MarketAgent(),
        PeopleAgent(),
        CustomerSentimentAgent(),
    ]
