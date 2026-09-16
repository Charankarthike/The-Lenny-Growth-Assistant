"""
Main agent orchestrator for handling user queries with skill-based routing.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.llm.base_provider import Message, CompletionResponse
from app.llm.provider_factory import get_llm_provider
from app.retrieval.retriever import Retriever, RetrievalResult
from app.agent.prompts import (
    CONVERSATIONAL_ASSISTANT_SYSTEM_PROMPT,
    SHIP_30_SYSTEM_PROMPT,
    get_conversational_prompt_with_context,
    get_ship_30_prompt_with_context
)
from app.db.repositories import MessageRepository
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    """Response from the agent."""
    content: str
    sources: List[RetrievalResult]
    skill_used: str
    token_usage: Optional[dict] = None
    metadata: Optional[dict] = None


class Agent:
    """
    Main agent orchestrator with skill-based routing.
    
    Workflow:
    1. Classify user intent
    2. Route to appropriate skill
    3. Retrieve relevant context
    4. Generate response
    5. Return with source attribution
    """
    
    def __init__(self, db: Session):
        """
        Initialize the agent.
        
        Args:
            db: Database session
        """
        self.db = db
        self.llm = get_llm_provider()
        self.retriever = Retriever(db)
        self.message_repo = MessageRepository(db)
        
        logger.info("agent_initialized")
    
    def process_query(
        self,
        query: str,
        session_id: str,
        stream: bool = False
    ) -> AgentResponse:
        """
        Process a user query and generate a response.
        
        Args:
            query: User's question
            session_id: Conversation session ID
            stream: Whether to stream the response
        
        Returns:
            Agent response with sources
        """
        logger.info("processing_query", query_length=len(query), session_id=session_id)
        
        # Step 1: Classify intent and route to skill
        skill = self._classify_intent(query)
        logger.info("intent_classified", skill=skill)
        
        # Step 2: Retrieve relevant context
        top_k = 10 if skill == "ship_30" else 5
        retrieval_results = self.retriever.retrieve(query, top_k=top_k)
        
        if not retrieval_results:
            # No relevant context found
            return AgentResponse(
                content="I don't have information about that in the available transcripts. Could you ask about product management, growth strategies, retention, or pricing?",
                sources=[],
                skill_used=skill,
                metadata={"no_context": True}
            )
        
        logger.info("context_retrieved", num_results=len(retrieval_results))
        
        # Step 3: Get conversation history
        conversation_history = self._get_conversation_history(session_id)
        
        # Step 4: Route to appropriate skill
        if skill == "ship_30":
            response = self._ship_30_skill(query, retrieval_results)
        else:  # conversational
            response = self._conversational_skill(
                query,
                retrieval_results,
                conversation_history
            )
        
        return response
    
    def _classify_intent(self, query: str) -> str:
        """
        Classify user intent to determine which skill to use.
        
        Args:
            query: User's question
        
        Returns:
            Skill name ('conversational' or 'ship_30')
        """
        query_lower = query.lower()
        
        # Ship 30 for 30 triggers
        ship_30_keywords = [
            "ship 30 for 30",
            "ship 30",
            "write an essay",
            "write a post",
            "create content",
            "generate an article",
            "write about"
        ]
        
        for keyword in ship_30_keywords:
            if keyword in query_lower:
                return "ship_30"
        
        # Default to conversational
        return "conversational"
    
    def _conversational_skill(
        self,
        query: str,
        retrieval_results: List[RetrievalResult],
        conversation_history: List[Message]
    ) -> AgentResponse:
        """
        Handle conversational Q&A with grounded answers.
        
        Args:
            query: User's question
            retrieval_results: Retrieved context
            conversation_history: Previous messages
        
        Returns:
            Agent response
        """
        # Format retrieved context
        context = self._format_context(retrieval_results)
        
        # Build conversation history string
        history_str = ""
        if conversation_history:
            recent_history = conversation_history[-4:]  # Last 2 exchanges
            history_str = "\n".join([
                f"{msg.role.capitalize()}: {msg.content}"
                for msg in recent_history
            ])
        
        # Build messages for LLM
        user_prompt = get_conversational_prompt_with_context(
            query=query,
            context=context,
            conversation_history=history_str
        )
        
        messages = [
            Message(role="system", content=CONVERSATIONAL_ASSISTANT_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt)
        ]
        
        # Generate response
        try:
            completion = self.llm.complete(messages)
            
            return AgentResponse(
                content=completion.content,
                sources=retrieval_results,
                skill_used="conversational",
                token_usage=completion.usage,
                metadata=completion.metadata
            )
        except Exception as e:
            logger.error("conversational_skill_failed", error=str(e))
            raise
    
    def _ship_30_skill(
        self,
        query: str,
        retrieval_results: List[RetrievalResult]
    ) -> AgentResponse:
        """
        Generate Ship 30 for 30 style content.
        
        Args:
            query: Topic for the essay
            retrieval_results: Retrieved context
        
        Returns:
            Agent response with formatted essay
        """
        # Format retrieved context
        context = self._format_context(retrieval_results)
        
        # Extract topic from query
        topic = self._extract_topic(query)
        
        # Build messages for LLM
        user_prompt = get_ship_30_prompt_with_context(
            topic=topic,
            context=context
        )
        
        messages = [
            Message(role="system", content=SHIP_30_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt)
        ]
        
        # Generate response with higher max tokens for essays
        try:
            completion = self.llm.complete(
                messages,
                max_tokens=3000  # Essays need more tokens
            )
            
            return AgentResponse(
                content=completion.content,
                sources=retrieval_results,
                skill_used="ship_30",
                token_usage=completion.usage,
                metadata=completion.metadata
            )
        except Exception as e:
            logger.error("ship_30_skill_failed", error=str(e))
            raise
    
    def _format_context(self, results: List[RetrievalResult]) -> str:
        """
        Format retrieval results as context for the LLM.
        
        Args:
            results: Retrieved chunks
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, result in enumerate(results, 1):
            episode_info = f"Episode {result.episode_number or '?'}"
            if result.guest_name:
                episode_info += f" with {result.guest_name}"
            episode_info += f": {result.title}"
            
            context_part = f"""[Source {i}] {episode_info}
{result.content}
"""
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def _get_conversation_history(self, session_id: str) -> List[Message]:
        """
        Get recent conversation history for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            List of recent messages
        """
        from uuid import UUID
        
        try:
            messages = self.message_repo.get_recent_messages(
                session_id=UUID(session_id),
                limit=settings.agent_max_context_messages
            )
            
            return [
                Message(role=msg.role, content=msg.content)
                for msg in messages
            ]
        except Exception as e:
            logger.warning("failed_to_get_conversation_history", error=str(e))
            return []
    
    def _extract_topic(self, query: str) -> str:
        """
        Extract the topic from a Ship 30 for 30 request.
        
        Args:
            query: User's query
        
        Returns:
            Extracted topic
        """
        # Remove common trigger phrases
        triggers = [
            "ship 30 for 30",
            "ship 30",
            "write an essay about",
            "write a post about",
            "create content about",
            "generate an article about",
            "write about"
        ]
        
        topic = query.lower()
        for trigger in triggers:
            topic = topic.replace(trigger, "")
        
        return topic.strip()
