"""Knowledge graph service — Neo4j integration with resilient in-memory fallback.

Provides:
- Node CRUD (Memory, Project, Concept, etc.)
- Relationship CRUD
- Neighbor traversal
- Shortest path finding
- Related memories lookup
- Resilient local graph fallback when Neo4j is offline
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from neo4j import AsyncDriver

from app.core.config import settings

logger = structlog.get_logger("synapseos.graph")


class GraphService:
    """Manages the knowledge graph in Neo4j with local fallback."""

    # Shared in-memory graph across instances when Neo4j is offline
    _nodes: dict[str, dict[str, Any]] = {}
    _relationships: list[dict[str, Any]] = []

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
        props["label"] = label

        # Always maintain in memory store
        self._nodes[node_id] = props

        try:
            query = f"""
            MERGE (n:{label} {{node_id: $node_id}})
            SET n += $props
            RETURN n
            """
            async with self.driver.session(database=settings.neo4j_database) as session:
                result = await session.run(query, node_id=node_id, props=props)
                record = await result.single()
                if record:
                    return dict(record["n"])
        except Exception as e:
            logger.debug("Saved node to local graph store", node_id=node_id, error=str(e))

        return props

    async def update_node(
        self,
        node_id: str,
        label: str,
        properties: dict,
    ) -> dict:
        """Update a node's properties."""
        if node_id in self._nodes:
            self._nodes[node_id].update(properties)

        try:
            query = f"""
            MATCH (n:{label} {{node_id: $node_id}})
            SET n += $props
            RETURN n
            """
            async with self.driver.session(database=settings.neo4j_database) as session:
                result = await session.run(query, node_id=node_id, props=properties)
                record = await result.single()
                if record:
                    return dict(record["n"])
        except Exception as e:
            logger.debug("Updated node in local graph store", node_id=node_id, error=str(e))

        return self._nodes.get(node_id, {})

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and all its relationships."""
        deleted = node_id in self._nodes
        self._nodes.pop(node_id, None)
        self._relationships = [
            r for r in self._relationships
            if r["source_id"] != node_id and r["target_id"] != node_id
        ]

        try:
            query = """
            MATCH (n {node_id: $node_id})
            DETACH DELETE n
            RETURN count(n) AS deleted
            """
            async with self.driver.session(database=settings.neo4j_database) as session:
                result = await session.run(query, node_id=node_id)
                record = await result.single()
                if record and (record["deleted"] or 0) > 0:
                    return True
        except Exception:
            pass

        return deleted

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict | None = None,
    ) -> dict:
        """Create a relationship between two nodes."""
        props = properties or {}
        rel_dict = {
            "source_id": source_id,
            "target_id": target_id,
            "type": relationship_type,
            "properties": props,
        }
        self._relationships.append(rel_dict)

        try:
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
        except Exception as e:
            logger.debug("Saved relationship in local graph store", error=str(e))

        return {"type": relationship_type, "properties": props}

    async def delete_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
    ) -> bool:
        """Delete a specific relationship between two nodes."""
        orig_len = len(self._relationships)
        self._relationships = [
            r for r in self._relationships
            if not (r["source_id"] == source_id and r["target_id"] == target_id and r["type"] == relationship_type)
        ]
        deleted = len(self._relationships) < orig_len

        try:
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
                if record and (record["deleted"] or 0) > 0:
                    return True
        except Exception:
            pass

        return deleted

    async def get_neighbors(
        self,
        node_id: str,
        relationship_type: str | None = None,
        direction: str = "both",
        limit: int = 50,
    ) -> list[dict]:
        """Get neighboring nodes of a given node."""
        try:
            rel_clause = f":{relationship_type}" if relationship_type else ""
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
                if nodes:
                    return nodes
        except Exception:
            pass

        # Local fallback
        neighbor_ids = set()
        for r in self._relationships:
            if relationship_type and r["type"] != relationship_type:
                continue
            if direction in ("out", "both") and r["source_id"] == node_id:
                neighbor_ids.add(r["target_id"])
            if direction in ("in", "both") and r["target_id"] == node_id:
                neighbor_ids.add(r["source_id"])

        nodes = []
        for nid in list(neighbor_ids)[:limit]:
            node_data = self._nodes.get(nid, {"node_id": nid})
            nodes.append({
                "node_id": nid,
                "labels": [node_data.get("label", "Entity")],
                "properties": node_data,
            })
        return nodes

    async def get_related_memories(
        self,
        memory_id: str,
        relationship_types: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get memories related to a given memory via the graph."""
        try:
            rel_clause = f":{'|'.join(relationship_types)}" if relationship_types else ""
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
                if memories:
                    return memories
        except Exception:
            pass

        neighbors = await self.get_neighbors(memory_id, limit=limit)
        return [{"node_id": n["node_id"], "properties": n["properties"]} for n in neighbors]

    async def get_graph_data(
        self,
        workspace_id: str,
        project_id: str | None = None,
        limit: int = 100,
    ) -> dict:
        """Get graph data for visualization (nodes and edges)."""
        nodes_map: dict[str, dict] = {}
        edges: list[dict] = []

        try:
            filter_clause = "AND m.project_id = $project_id" if project_id else ""
            params: dict = {"workspace_id": workspace_id, "limit": limit}
            if project_id:
                params["project_id"] = project_id

            query = f"""
            MATCH (m:Memory)
            WHERE m.workspace_id = $workspace_id {filter_clause}
            OPTIONAL MATCH (m)-[r]->(target)
            RETURN m AS source_node, type(r) AS rel_type, target AS target_node
            LIMIT $limit
            """
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

                        rel_type = record["rel_type"] or "RELATED_TO"
                        edges.append({
                            "id": f"{sid}-{tid}",
                            "source": sid,
                            "target": tid,
                            "label": rel_type,
                        })

            if nodes_map:
                return {"nodes": list(nodes_map.values()), "edges": edges}
        except Exception:
            pass

        # In-memory graph visualization fallback
        for nid, data in self._nodes.items():
            if data.get("workspace_id") == workspace_id:
                if project_id and data.get("project_id") != project_id:
                    continue
                nodes_map[nid] = {
                    "id": nid,
                    "label": data.get("title", nid[:20]),
                    "type": data.get("label", "memory").lower(),
                    "memory_type": data.get("memory_type", "knowledge"),
                }

        for r in self._relationships:
            sid = r["source_id"]
            tid = r["target_id"]
            if sid in nodes_map or tid in nodes_map:
                edges.append({
                    "id": f"{sid}-{tid}",
                    "source": sid,
                    "target": tid,
                    "label": r["type"],
                })

        return {"nodes": list(nodes_map.values()), "edges": edges}
