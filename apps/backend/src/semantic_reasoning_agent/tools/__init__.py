"""First-class execution units — AGENTS.md §9.

A ``Tool`` consumes a ``ToolEnvelope`` (Standard Tool Input) and — via the
``ToolRuntime`` wrapper — produces a ``ToolResult`` (Standard Tool Output).
Each tool is paired with a declarative ``ToolSpec`` registered in the
``ToolRegistry`` so the LLM runtime can surface it for native function calling.

Families (``document``, ``retrieval``, ``ontology``, ``graph``, ``web``, ``mcp``,
``artifact``, ``admin``) follow the phase roadmap in AGENTS.md §18.
"""
