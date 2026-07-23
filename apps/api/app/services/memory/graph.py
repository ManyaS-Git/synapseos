"""Knowledge graph service — Neo4j integration for relationship memory.

Provides:
- Node CRUD (Memory, Project, Concept, etc.)
- Relationship CRUD
- Neighbor traversal
- Shortest path finding
- Related memories lookup
"""

from __future__ import annotations

import uuid

import structlog
from neo4j import AsyncDriver

from app.core.config import settings

logger = structlog.get_logger("synapseos.graph")


class GraphService:
    """Manages the knowledge graph in Neo4j."""

    def __init__(self, driver: AsyncDriver | None = None):
        self._driver = driver

    @property
    def driver(self) -> AsyncDriver:
        if self._driver is None:
            from app.core.database import neo4j_manager
            self._driver = neo4j_manager.driver
        return self._driver

    async def create_node(
        self,
        node_id: str,
        label: str,
        properties: dict | None = None,
    ) -> dict:
        """Create a node in the graph."""
        props = properties or {}
        props["node_id"] = node_id

        query = f"""
        MERGE (n:{label} {{node_id: $node_id}})
        SET n += $props
        RETURN n
        """
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, node_id=node_id, props=props)
            record = await result.single()
            return dict(record["n"]) if record else {}

    async def update_node(
        self,
        node_id: str,
        label: str,
        properties: dict,
    ) -> dict:
        """Update a node's properties."""
        query = f"""
        MATCH (n:{label} {{node_id: $node_id}})
        SET n += $props
        RETURN n
        """
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, node_id=node_id, props=properties)
            record = await result.single()
            return dict(record["n"]) if record else {}

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and all its relationships."""
        query = """
        MATCH (n {node_id: $node_id})
        DETACH DELETE n
        RETURN count(n) AS deleted
        """
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            return (record["deleted"] or 0) > 0

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict | None = None,
    ) -> dict:
        """Create a relationship between two nodes."""
        props = properties or {}

        query = f"""
        MATCH (a {{node_id: $source_id}})
        MATCH (b {{node_id: $target_id}})
        MERGE (a)-[r:{relationship_type}]->(b)
        SET r += $props
        RETURN type(r) AS type, properties(r) AS props
        """
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                query, source_id=source_id, target_id=target_id, props=props
            )
            record = await result.single()
            if record:
                return {"type": record["type"], "properties": record["props"]}
            return {}

    async def delete_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
    ) -> bool:
        """Delete a specific relationship between two nodes."""
        query = f"""
        MATCH (a {{node_id: $source_id}})-[r:{relationship_type}]->(b {{node_id: $target_id}})
        DELETE r
        RETURN count(r) AS deleted
        """
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(
                query, source_id=source_id, target_id=target_id
            )
            record = await result.single()
            return (record["deleted"] or 0) > 0

    async def get_neighbors(
        self,
        node_id: str,
        relationship_type: str | None = None,
        direction: str = "both",
        limit: int = 50,
    ) -> list[dict]:
        """Get neighboring nodes of a given node."""
        rel_clause = ""
        if relationship_type:
            rel_clause = f":{relationship_type}"

        if direction == "out":
            path_pattern = f"(n {{node_id: $node_id}})-[{rel_clause}]->(m)"
        elif direction == "in":
            path_pattern = f"(m)-[{rel_clause}]->(n {{node_id: $node_id}})"
        else:
            path_pattern = f"(n {{node_id: $node_id}})-[{rel_clause}]-(m)"

        query = f"""
        MATCH {path_pattern}
        RETURN DISTINCT m.node_id AS node_id, labels(m) AS labels, properties(m) AS props
        LIMIT $limit
        """

        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, node_id=node_id, limit=limit)
            nodes = []
            async for record in result:
                nodes.append({
                    "node_id": record["node_id"],
                    "labels": record["labels"],
                    "properties": record["props"],
                })
            return nodes

    async def shortest_path(
        self,
        source_id: str,
        target_id: str,
    ) -> list[dict] | None:
        """Find the shortest path between two nodes."""
        query = """
        MATCH path = shortestPath(
            (a {node_id: $source_id})-[*]-(b {node_id: $target_id})
        )
        RETURN [n IN nodes(path) | n.node_id] AS node_ids,
               [r IN relationships(path) | type(r)] AS rel_types
        LIMIT 1
        """
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, source_id=source_id, target_id=target_id)
            record = await result.single()
            if record:
                return {
                    "node_ids": record["node_ids"],
                    "rel_types": record["rel_types"],
                }
            return None

    async def get_related_memories(
        self,
        memory_id: str,
        relationship_types: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get memories related to a given memory via the graph."""
        rel_clause = ""
        if relationship_types:
            types_str = "|".join(relationship_types)
            rel_clause = f":{types_str}"

        query = f"""
        MATCH (m:Memory {{node_id: $memory_id}})-[{rel_clause}]-(related:Memory)
        RETURN related.node_id AS node_id, properties(related) AS props
        LIMIT $limit
        """

        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, memory_id=memory_id, limit=limit)
            memories = []
            async for record in result:
                memories.append({
                    "node_id": record["node_id"],
                    "properties": record["props"],
                })
            return memories

    async def get_graph_data(
        self,
        workspace_id: str,
        project_id: str | None = None,
        limit: int = 100,
    ) -> dict:
        """Get graph data for visualization (nodes and edges)."""
        filter_clause = ""
        params: dict = {"workspace_id": workspace_id, "limit": limit}

        if project_id:
            filter_clause = "AND m.project_id = $project_id"
            params["project_id"] = project_id

        query = f"""
        MATCH (m:Memory)
        WHERE m.workspace_id = $workspace_id {filter_clause}
        OPTIONAL MATCH (m)-[r]->(target)
        RETURN m AS source_node, type(r) AS rel_type, target AS target_node
        LIMIT $limit
        """

        nodes_map: dict[str, dict] = {}
        edges: list[dict] = []

        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, **params)
            async for record in result:
                source = record["source_node"]
                if source and source.get("node_id"):
                    sid = source["node_id"]
                    if sid not in nodes_map:
                        nodes_map[sid] = {
                            "id": sid,
                            "label": source.get("title", sid[:20]),
                            "type": "memory",
                            "memory_type": source.get("memory_type"),
                        }

                target = record["target_node"]
                if target and target.get("node_id"):
                    tid = target["node_id"]
                    if tid not in nodes_map:
                        nodes_map[tid] = {
                            "id": tid,
                            "label": target.get("title", tid[:20]),
                            "type": target.get("label", "entity"),
                        }

                    rel_type = record["rel_type"]
                    edges.append({
                        "id": f"{sid}-{tid}",
                        "source": sid,
                        "target": tid,
                        "label": rel_type,
                    })

        return {"nodes": list(nodes_map.values()), "edges": edges}
