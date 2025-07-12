# src/agents.py
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage

# Import the custom callback handler to check its type
from .callbacks import StreamlitCallbackHandler

# Initialize the LLM with Groq
llm = ChatGroq(temperature=0, model_name="llama3-8b-8192", api_key=os.environ["GROQ_API_KEY"])

# --- Tool Schemas for Structured Output ---
class RelevanceScore(BaseModel):
    """A score for a single candidate based on skills and experience."""
    candidate_name: str = Field(description="The full name of the candidate.")
    score: int = Field(description="A relevance score from 0 to 100 based on ideal criteria.")
    justification: str = Field(description="A brief justification for the assigned score.")

class DiversityAnalysis(BaseModel):
    """An analysis of team diversity based on a selection of candidates."""
    diversity_score: int = Field(description="A diversity score from 0 to 100 for a potential team of 5 derived from the list.")
    justification: str = Field(description="An explanation of the diversity score, considering location and educational background.")

class FinalSelection(BaseModel):
    """The final selection of top 5 candidates with summaries explaining the choice."""
    selected_candidates: list[str] = Field(description="A list of the names of the 5 finally selected candidates.")
    summaries: list[str] = Field(description="A list of concise summaries explaining why each candidate was chosen for the team.")

# --- Agent Functions (Updated for Scalability) ---

def sourcing_agent(state):
    """Sourcing Agent: Loads and prepares candidate data."""
    print("---AGENT: Sourcing Agent---")
    candidate_data = state['candidates']
    return {"candidates": candidate_data, "parsed_profiles": "\n---\n".join([str(c) for c in candidate_data])}

def screening_agent(state, config):
    """
    Screening Agent: Processes the ENTIRE list of candidates in a loop to avoid recursion errors.
    """
    print("---AGENT: Screening Agent (Batch Processing)---")
    
    all_candidates = state['candidates']
    all_scores = []
    
    # --- START OF FIX ---
    # Get the CallbackManager from the config
    callback_manager = config.get("callbacks")
    callback_handler = None
    if callback_manager:
        # The callback manager holds a list of handlers. Find our custom one.
        for handler in callback_manager.handlers:
            if isinstance(handler, StreamlitCallbackHandler):
                callback_handler = handler
                break
    # --- END OF FIX ---

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="You are a professional hiring screener. Your task is to evaluate a single candidate profile based on a set of ideal criteria for a tech startup. The ideal candidate has a strong background in technology (like Python, React, AWS, or Data Science) or product management. A degree from a top 50 university is a plus but not required. Score the candidate from 0 to 100 based on their relevance to these criteria and provide a brief justification."
            ),
            ("human", "Please score the following candidate:\n\n{profile}"),
        ]
    )
    
    structured_llm = llm.with_structured_output(RelevanceScore)
    chain = prompt | structured_llm
    
    # Loop through each candidate, making one API call per candidate
    for candidate in all_candidates:
        try:
            result = chain.invoke({"profile": str(candidate)})
            all_scores.append(result)
        except Exception as e:
            print(f"Error processing candidate {candidate.get('name', 'N/A')}: {e}")
            all_scores.append(RelevanceScore(candidate_name=candidate.get('name', 'N/A'), score=0, justification="Error during processing."))

        # Update the UI via the callback handler if it was found
        if callback_handler:
            callback_handler.on_agent_step()
            
    return {"all_relevance_scores": all_scores}

def diversity_agent(state):
    """D&I Agent: Analyzes the diversity of all scored candidates."""
    print("---AGENT: Diversity & Inclusion Agent---")
    
    all_scores = state['all_relevance_scores']
    top_candidates_scores = sorted(all_scores, key=lambda x: x.score, reverse=True)
    
    analysis_subset = top_candidates_scores[:20]

    top_profiles_str = "\n---\n".join([f"Name: {s.candidate_name}, Score: {s.score}, Location: {c.get('location', 'N/A')}, School: {c.get('education', {}).get('degrees', [{}])[0].get('school', 'N/A')}" for s in analysis_subset for c in state['candidates'] if c['name'] == s.candidate_name])

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="You are a Diversity and Inclusion specialist. Analyze the following list of top-scoring candidates to form a team of 5. Your goal is to ensure a balanced and diverse team. Consider diversity in location and educational background (e.g., mix of top-tier and other universities). Provide a holistic diversity score from 0 to 100 for a potential team of 5 derived from this list, and justify your score."
            ),
            ("human", "Analyze this list for diversity to help form a team of 5:\n\n{profiles}"),
        ]
    )
    
    structured_llm = llm.with_structured_output(DiversityAnalysis)
    chain = prompt | structured_llm
    result = chain.invoke({"profiles": top_profiles_str})
    
    return {"diversity_analysis": result}

def hiring_manager_agent(state):
    """Hiring Manager Agent: Makes the final selection based on all inputs."""
    print("---AGENT: Hiring Manager Agent---")
    
    relevance_scores_str = "\n".join([f"Name: {s.candidate_name}, Score: {s.score}" for s in state['all_relevance_scores']])
    diversity_analysis_str = f"Diversity Score: {state['diversity_analysis'].diversity_score}, Justification: {state['diversity_analysis'].justification}"
    
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content="You are the Hiring Manager. Your task is to select the top 5 candidates for a new startup team. You have been provided with relevance scores for all candidates and a diversity analysis. Your final team should be a strong mix of technical talent, product/business skills, and diversity. Select the best 5 candidates and provide a concise summary for each, explaining exactly why they were chosen for the team."
            ),
            ("human", "Based on the following data, make your final selection of 5 candidates:\n\nRelevance Scores (Top 20 shown for brevity):\n{relevance_scores_subset}\n\nDiversity Analysis:\n{diversity_analysis}"),
        ]
    )
    
    structured_llm = llm.with_structured_output(FinalSelection)
    chain = prompt | structured_llm
    
    top_scores_for_prompt = sorted(state['all_relevance_scores'], key=lambda x: x.score, reverse=True)[:20]
    top_scores_str = "\n".join([f"Name: {s.candidate_name}, Score: {s.score}, Justification: {s.justification}" for s in top_scores_for_prompt])

    result = chain.invoke({
        "relevance_scores_subset": top_scores_str,
        "diversity_analysis": diversity_analysis_str,
    })
    
    return {"final_selection": result}