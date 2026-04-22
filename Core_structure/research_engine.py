
# ==================================================
# research_engine.py — Vivie Research Intelligence
# Deep research, knowledge graphs, insights
# Never existed before in a personal AI system
# ==================================================

import json
import os
import datetime
import threading
import time
from typing import Any

from Brain.cl_brain     import Main_Brain
from Features.web_search import search_web
from knowledge_core.rag_store import store_knowledge

BASE_DIR         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_DIR     = os.path.join(BASE_DIR, "data", "research")
GRAPH_FILE       = os.path.join(RESEARCH_DIR, "knowledge_graph.json")
SESSIONS_FILE    = os.path.join(RESEARCH_DIR, "research_sessions.json")
INSIGHTS_FILE    = os.path.join(RESEARCH_DIR, "insights.json")


# ─────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────

def _init_dirs():
    os.makedirs(RESEARCH_DIR, exist_ok=True)

def _load(path: str, default) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save(path: str, data: Any):
    try:
        _init_dirs()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ResearchEngine] Save error: {e}")


# ─────────────────────────────────────────────────
# KNOWLEDGE GRAPH
# Maps connections between topics Vivie has researched
# ─────────────────────────────────────────────────

class KnowledgeGraph:
    """
    Vivie's knowledge graph.
    Nodes = topics
    Edges = relationships between topics
    """

    def __init__(self):
        self._graph = _load(GRAPH_FILE, {"nodes": {}, "edges": []})

    def add_node(self, topic: str, summary: str, category: str = "general"):
        """Add or update a topic node."""
        topic_key = topic.lower().strip()
        self._graph["nodes"][topic_key] = {
            "topic":      topic,
            "summary":    summary[:300],
            "category":   category,
            "added":      datetime.date.today().isoformat(),
            "visit_count": self._graph["nodes"].get(topic_key, {}).get("visit_count", 0) + 1
        }
        _save(GRAPH_FILE, self._graph)

    def add_edge(self, topic_a: str, topic_b: str, relationship: str):
        """Connect two topics with a relationship."""
        edge = {
            "from":         topic_a.lower().strip(),
            "to":           topic_b.lower().strip(),
            "relationship": relationship,
            "strength":     1
        }

        # Increase strength if already exists
        for existing in self._graph["edges"]:
            if (existing["from"] == edge["from"] and
                existing["to"]   == edge["to"]):
                existing["strength"] += 1
                _save(GRAPH_FILE, self._graph)
                return

        self._graph["edges"].append(edge)
        _save(GRAPH_FILE, self._graph)

    def get_connected_topics(self, topic: str, depth: int = 2) -> list:
        """Get all topics connected to a given topic."""
        topic_key = topic.lower().strip()
        connected = set()
        queue     = [topic_key]

        for _ in range(depth):
            next_queue = []
            for t in queue:
                for edge in self._graph["edges"]:
                    if edge["from"] == t and edge["to"] not in connected:
                        connected.add(edge["to"])
                        next_queue.append(edge["to"])
                    elif edge["to"] == t and edge["from"] not in connected:
                        connected.add(edge["from"])
                        next_queue.append(edge["from"])
            queue = next_queue

        # Return full node data
        result = []
        for t in connected:
            if t in self._graph["nodes"]:
                result.append(self._graph["nodes"][t])
        return result

    def get_most_researched(self, top_k: int = 5) -> list:
        """Return most visited topics."""
        nodes = list(self._graph["nodes"].values())
        nodes.sort(key=lambda x: x.get("visit_count", 0), reverse=True)
        return nodes[:top_k]

    def get_graph_summary(self) -> str:
        """Human readable graph summary."""
        nodes = self._graph["nodes"]
        edges = self._graph["edges"]

        if not nodes:
            return "Knowledge graph is empty. Research some topics to build it."

        summary  = f"Knowledge graph contains {len(nodes)} topics and {len(edges)} connections.\n\n"
        summary += "Most researched topics:\n"

        top = self.get_most_researched(5)
        for node in top:
            summary += f"  • {node['topic']} (visited {node['visit_count']} times)\n"

        return summary

    def visualize_connections(self, topic: str) -> str:
        """Show connections for a specific topic."""
        connected = self.get_connected_topics(topic)
        if not connected:
            return f"No connections found for '{topic}' yet."

        lines = [f"Connections for '{topic}':"]
        for node in connected:
            lines.append(f"  → {node['topic']}: {node['summary'][:80]}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────
# RESEARCH SESSION
# ─────────────────────────────────────────────────

class ResearchSession:
    """Single research session with full history."""

    def __init__(self, query: str):
        self.query    = query
        self.started  = datetime.datetime.now().isoformat()
        self.sources  = []
        self.findings = []
        self.insights = []
        self.graph_nodes_added = []

    def to_dict(self) -> dict:
        return {
            "query":    self.query,
            "started":  self.started,
            "sources":  self.sources,
            "findings": self.findings,
            "insights": self.insights,
            "nodes":    self.graph_nodes_added
        }


# ─────────────────────────────────────────────────
# DEEP RESEARCH ENGINE
# ─────────────────────────────────────────────────

class ResearchEngine:

    def __init__(self):
        self.graph = KnowledgeGraph()
        _init_dirs()

    # ─────────────────────────────────────────────
    # DEEP RESEARCH
    # ─────────────────────────────────────────────

    def deep_research(self, query: str, depth: int = 3) -> str:
        """
        Comprehensive multi-angle research.

        depth: how many search angles to explore
        Returns: complete research report
        """
        print(f"[ResearchEngine] Starting deep research: '{query}'")
        session = ResearchSession(query)

        # ── Step 1: Check previous research ───────
        prev_context = self._get_previous_research(query)
        connected    = self.graph.get_connected_topics(query)

        # ── Step 2: Multi-angle search ─────────────
        search_angles = self._generate_search_angles(query, depth)
        all_content   = ""

        for angle in search_angles:
            print(f"[ResearchEngine] Searching: '{angle}'")
            results = search_web(angle)
            if results:
                for r in results[:2]:
                    title   = r.get("title", "")
                    content = r.get("content", "") or r.get("snippet", "")
                    if content:
                        all_content += f"Source: {title}\n{content[:500]}\n\n"
                        session.sources.append(title)
            time.sleep(0.5)  # avoid rate limits

        if not all_content:
            return self._fallback_research(query)

        # ── Step 3: Extract key findings ──────────
        findings = self._extract_findings(query, all_content)
        session.findings.append(findings) if findings else None

        # ── Step 4: Generate insights ─────────────
        insights = self._generate_insights(
            query, findings, prev_context, connected
        )
        session.insights.append(insights) if insights else None

        # ── Step 5: Build knowledge graph ─────────
        related_topics = self._extract_related_topics(query, findings)
        for topic, relationship in related_topics:
            self.graph.add_edge(query, topic, relationship)
            self.graph.add_node(topic, findings[:200], "research")
            session.graph_nodes_added.append(topic)

        self.graph.add_node(query, findings[:200], "research")

        # ── Step 6: Build final report ─────────────
        report = self._build_report(
            query, findings, insights, related_topics,
            prev_context, session.sources
        )

        # ── Step 7: Save session + store in RAG ───
        self._save_session(session)
        store_knowledge(
            f"Research on {query}:\n{findings[:500]}",
            {"source": "research_engine", "topic": query}
        )

        print(f"[ResearchEngine] Research complete. {len(session.sources)} sources.")
        return report

    # ─────────────────────────────────────────────
    # GENERATE SEARCH ANGLES
    # Multiple perspectives on one topic
    # ─────────────────────────────────────────────

    def _generate_search_angles(self, query: str, depth: int) -> list:
        """Generate multiple search angles for comprehensive coverage."""
        base_angles = [
            query,
            f"{query} latest 2026",
            f"{query} explained simply",
            f"{query} advanced concepts",
            f"{query} real world applications",
            f"{query} research papers",
            f"how does {query} work",
        ]
        return base_angles[:depth]

    # ─────────────────────────────────────────────
    # EXTRACT FINDINGS
    # ─────────────────────────────────────────────

    def _extract_findings(self, query: str, raw_content: str) -> str:
        """Extract structured findings from raw web content."""
        prompt = f"""You are Vivie's Research Intelligence system.

Topic: {query}

Raw sources:
{raw_content[:3000]}

Extract and structure the key findings:
1. Core facts and definitions
2. Recent developments (2025-2026)
3. Key statistics or data points
4. Expert opinions or consensus
5. Controversies or open questions

Be comprehensive but factual. No hallucination."""

        return Main_Brain(prompt) or "Research findings unavailable."

    # ─────────────────────────────────────────────
    # GENERATE INSIGHTS
    # This is what makes Vivie's research unprecedented
    # ─────────────────────────────────────────────

    def _generate_insights(
        self,
        query:        str,
        findings:     str,
        prev_context: str,
        connected:    list
    ) -> str:
        """
        Generate insights that go beyond summarization.
        Connects current research to previous knowledge.
        This is what no other personal AI does.
        """
        connected_str = ""
        if connected:
            connected_str = "Previously researched related topics:\n"
            for node in connected[:3]:
                connected_str += f"  - {node['topic']}: {node['summary'][:100]}\n"

        prev_str = ""
        if prev_context:
            prev_str = f"Previous research on this topic:\n{prev_context[:500]}\n"

        prompt = f"""You are Vivie's Insight Engine — the part of Vivie that thinks beyond facts.

Current research topic: {query}

Findings:
{findings[:1500]}

{connected_str}
{prev_str}

Generate genuine insights that go beyond the facts:
1. What patterns do you notice that aren't explicitly stated?
2. How does this connect to related topics the user has researched?
3. What implications does this have for the user specifically?
4. What questions does this raise that aren't answered yet?
5. What would a true expert notice that a beginner would miss?

Be genuinely insightful. This is not a summary — it's original thinking."""

        return Main_Brain(prompt) or ""

    # ─────────────────────────────────────────────
    # EXTRACT RELATED TOPICS
    # Builds the knowledge graph automatically
    # ─────────────────────────────────────────────

    def _extract_related_topics(self, query: str, findings: str) -> list:
        """Extract related topics to build knowledge graph."""
        prompt = f"""From this research on '{query}', identify related topics.

Findings excerpt:
{findings[:1000]}

List up to 5 related topics and their relationship to '{query}'.
Format each line as: TOPIC|RELATIONSHIP
Example: machine learning|is a subset of
Example: neural networks|is used in

Only return the formatted lines, nothing else."""

        response = Main_Brain(prompt) or ""
        result   = []

        for line in response.strip().split("\n"):
            if "|" in line:
                parts = line.strip().split("|")
                if len(parts) == 2:
                    topic        = parts[0].strip()
                    relationship = parts[1].strip()
                    if topic and relationship:
                        result.append((topic, relationship))

        return result[:5]

    # ─────────────────────────────────────────────
    # BUILD FINAL REPORT
    # ─────────────────────────────────────────────

    def _build_report(
        self,
        query:          str,
        findings:       str,
        insights:       str,
        related_topics: list,
        prev_context:   str,
        sources:        list
    ) -> str:

        report  = f"DEEP RESEARCH: {query.upper()}\n"
        report += "=" * 50 + "\n\n"

        report += "KEY FINDINGS:\n"
        report += findings[:800] + "\n\n"

        if insights:
            report += "INSIGHTS:\n"
            report += insights[:600] + "\n\n"

        if related_topics:
            report += "CONNECTED TOPICS:\n"
            for topic, rel in related_topics[:3]:
                report += f"  • {topic} — {rel} {query}\n"
            report += "\n"

        if prev_context:
            report += "BUILDING ON PREVIOUS RESEARCH:\n"
            report += prev_context[:200] + "\n\n"

        if sources:
            report += f"SOURCES: {len(sources)} sources consulted\n"
            for s in sources[:3]:
                report += f"  • {s[:60]}\n"

        return report

    # ─────────────────────────────────────────────
    # PREVIOUS RESEARCH
    # ─────────────────────────────────────────────

    def _get_previous_research(self, query: str) -> str:
        """Check if we've researched this topic before."""
        sessions = _load(SESSIONS_FILE, [])
        query_lower = query.lower()

        for session in reversed(sessions[-20:]):
            if query_lower in session.get("query", "").lower():
                findings = session.get("findings", "")
                if findings:
                    return f"Previous research on this: {findings[:300]}"
        return ""

    # ─────────────────────────────────────────────
    # SAVE SESSION
    # ─────────────────────────────────────────────

    def _save_session(self, session: ResearchSession):
        sessions = _load(SESSIONS_FILE, [])
        sessions.append(session.to_dict())
        sessions = sessions[-50:]  # keep last 50
        _save(SESSIONS_FILE, sessions)

    # ─────────────────────────────────────────────
    # FALLBACK
    # ─────────────────────────────────────────────

    def _fallback_research(self, query: str) -> str:
        prompt = f"""Research this topic thoroughly: {query}

Provide:
1. Comprehensive overview
2. Key facts and recent developments
3. Important insights
4. Connections to related topics

Be thorough and genuinely informative."""
        return Main_Brain(prompt) or "Research unavailable."

    # ─────────────────────────────────────────────
    # COMPARE TOPICS
    # Research two topics and compare them
    # ─────────────────────────────────────────────

    def compare_topics(self, topic_a: str, topic_b: str) -> str:
        """Deep comparison of two topics."""
        print(f"[ResearchEngine] Comparing: '{topic_a}' vs '{topic_b}'")

        # Research both
        results_a = search_web(topic_a)
        results_b = search_web(topic_b)

        content_a = ""
        content_b = ""

        if results_a:
            for r in results_a[:2]:
                content_a += r.get("content", "") or r.get("snippet", "") + "\n"

        if results_b:
            for r in results_b[:2]:
                content_b += r.get("content", "") or r.get("snippet", "") + "\n"

        prompt = f"""You are Vivie's Research Intelligence.

Compare these two topics deeply:

Topic A: {topic_a}
{content_a[:1000]}

Topic B: {topic_b}
{content_b[:1000]}

Provide:
1. Key similarities
2. Key differences
3. When to use each
4. Your verdict — which is better for what purpose
5. An insight that goes beyond the obvious comparison"""

        result = Main_Brain(prompt) or "Comparison unavailable."

        # Add to graph
        self.graph.add_edge(topic_a, topic_b, "compared with")
        self.graph.add_node(topic_a, content_a[:200])
        self.graph.add_node(topic_b, content_b[:200])

        return result

    # ─────────────────────────────────────────────
    # RESEARCH HISTORY
    # ─────────────────────────────────────────────

    def get_research_history(self, top_k: int = 5) -> str:
        """Return recent research sessions."""
        sessions = _load(SESSIONS_FILE, [])
        if not sessions:
            return "No research sessions yet."

        lines = [f"Last {min(top_k, len(sessions))} research sessions:"]
        for session in reversed(sessions[-top_k:]):
            query   = session.get("query", "")
            started = session.get("started", "")[:10]
            sources = len(session.get("sources", []))
            lines.append(f"  • [{started}] {query} ({sources} sources)")

        return "\n".join(lines)

    # ─────────────────────────────────────────────
    # KNOWLEDGE GRAPH SUMMARY
    # ─────────────────────────────────────────────

    def get_knowledge_map(self, topic: str | None = None) -> str:
        """Show knowledge graph for a topic or overall."""
        if topic:
            return self.graph.visualize_connections(topic)
        return self.graph.get_graph_summary()


# ─────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────

_engine: ResearchEngine | None = None

def get_research_engine() -> ResearchEngine:
    global _engine
    if _engine is None:
        _engine = ResearchEngine()
    return _engine