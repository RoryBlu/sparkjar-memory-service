# services/memory-service/mcp_server.py
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
import json
import os
from uuid import UUID

class MemoryMCPServer:
    """MCP wrapper for SparkJar Memory Service"""
    
    def __init__(self, external_api_url: str = "https://localhost:8443"):
        self.external_api_url = external_api_url
        self.server = Server("sparkjar-memory-server")
        self.auth_token = os.getenv("MEMORY_SERVICE_TOKEN", "")
        self.setup_handlers()
    
    async def _call_external_api(self, endpoint: str, method: str = "POST", data: Any = None):
        """Call the external API with proper authentication"""
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(verify=False) as client:  # In production, use proper SSL
            try:
                if method == "POST":
                    response = await client.post(
                        f"{self.external_api_url}{endpoint}", 
                        json=data,
                        headers=headers,
                        timeout=30.0
                    )
                elif method == "DELETE":
                    response = await client.delete(
                        f"{self.external_api_url}{endpoint}",
                        json=data,
                        headers=headers,
                        timeout=30.0
                    )
                elif method == "GET":
                    response = await client.get(
                        f"{self.external_api_url}{endpoint}",
                        headers=headers,
                        params=data if data else {},
                        timeout=30.0
                    )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                return {"error": f"API error: {e.response.status_code} - {e.response.text}"}
            except Exception as e:
                return {"error": f"Request failed: {str(e)}"}
    
    def setup_handlers(self):
        """Setup MCP tool handlers"""
        self.setup_tools()
        self.setup_resources()
        self.setup_prompts()
    
    def setup_tools(self):
        """Setup MCP tools"""
        
        @self.server.tool("create_memory_entities")
        async def create_entities(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Create memory entities
            
            Args:
                entities: List of entities with name, entityType, and observations
            """
            result = await self._call_external_api("/memory/entities", data=entities)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("create_memory_relations")
        async def create_relations(relations: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Create relationships between entities
            
            Args:
                relations: List of relations with from_entity_name, to_entity_name, relationType
            """
            result = await self._call_external_api("/memory/relations", data=relations)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("search_memory")
        async def search_memory(
            query: str,
            entity_types: Optional[List[str]] = None,
            limit: int = 10,
            min_confidence: float = 0.7
        ) -> Dict[str, Any]:
            """Search memory using semantic similarity
            
            Args:
                query: Search query text
                entity_types: Optional filter by entity types (array)
                limit: Maximum results to return
                min_confidence: Minimum similarity confidence (0-1)
            """
            params = {
                "query": query,
                "limit": limit,
                "min_confidence": min_confidence
            }
            if entity_types:
                params["entity_types"] = entity_types
            
            result = await self._call_external_api("/memory/search", data=params)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("add_observations")
        async def add_observations(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Add observations to existing entities
            
            Args:
                observations: List with entityName and contents (observations to add)
            """
            result = await self._call_external_api("/memory/observations", data=observations)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("get_entities")
        async def get_entities(names: List[str]) -> Dict[str, Any]:
            """Get specific entities by name
            
            Args:
                names: List of entity names to retrieve
            """
            result = await self._call_external_api("/memory/nodes", data=names)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("read_memory_graph")
        async def read_graph() -> Dict[str, Any]:
            """Get all entities and relations for the authenticated actor"""
            result = await self._call_external_api("/memory/graph", method="GET")
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("delete_entities")
        async def delete_entities(entity_names: List[str]) -> Dict[str, Any]:
            """Delete entities and their relations
            
            Args:
                entity_names: List of entity names to delete
            """
            result = await self._call_external_api("/memory/entities", method="DELETE", data=entity_names)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("delete_relations")
        async def delete_relations(relations: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Delete specific relations
            
            Args:
                relations: List with from_entity_name, to_entity_name, relation_type
            """
            result = await self._call_external_api("/memory/relations", method="DELETE", data=relations)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("remember_conversation")
        async def remember_conversation(
            conversation_text: str,
            participants: List[str],
            context: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Extract and store knowledge from conversation transcripts
            
            Args:
                conversation_text: Full conversation transcript
                participants: List of participant names/IDs
                context: Meeting type, date, purpose
            """
            data = {
                "conversation_text": conversation_text,
                "participants": participants,
                "context": context
            }
            result = await self._call_external_api("/memory/remember_conversation", data=data)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("find_connections")
        async def find_connections(
            from_entity: str,
            to_entity: Optional[str] = None,
            max_hops: int = 3,
            relationship_types: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """Find paths between entities using graph traversal
            
            Args:
                from_entity: Starting entity name
                to_entity: Target entity name (optional - finds all connections if not specified)
                max_hops: Maximum relationship hops to traverse
                relationship_types: Filter by specific relationship types
            """
            data = {
                "from_entity": from_entity,
                "max_hops": max_hops
            }
            if to_entity:
                data["to_entity"] = to_entity
            if relationship_types:
                data["relationship_types"] = relationship_types
            
            result = await self._call_external_api("/memory/find_connections", data=data)
            return {"success": "error" not in result, "result": result}
        
        @self.server.tool("get_client_insights")
        async def get_client_insights() -> Dict[str, Any]:
            """Generate insights and analytics about the client's knowledge graph
            
            Returns insights about knowledge gaps, skill distribution,
            underutilized expertise, and collaboration opportunities.
            """
            result = await self._call_external_api("/memory/insights", method="GET")
            return {"success": "error" not in result, "result": result}
    
    def setup_resources(self):
        """Setup MCP resources for browsing memory content"""
        
        @self.server.resource("memory://entities/{type}")
        async def get_entities_by_type(type: str) -> Dict[str, Any]:
            """Browse entities by type"""
            # Search for all entities of a specific type
            result = await self._call_external_api("/memory/search", data={
                "query": "",  # Empty query to get all
                "entity_types": [type],
                "limit": 100
            })
            
            if "error" in result:
                return {"error": result["error"]}
            
            return {
                "mimeType": "application/json",
                "text": json.dumps({
                    "type": type,
                    "entities": result,
                    "count": len(result)
                }, indent=2)
            }
        
        @self.server.resource("memory://relationships/{type}")
        async def get_relationships_by_type(type: str) -> Dict[str, Any]:
            """Browse relationships by type"""
            # Get full graph and filter relationships
            result = await self._call_external_api("/memory/graph", method="GET")
            
            if "error" in result:
                return {"error": result["error"]}
            
            # Filter relationships by type
            filtered_relations = [
                rel for rel in result.get("relations", [])
                if rel.get("relation_type") == type
            ]
            
            return {
                "mimeType": "application/json",
                "text": json.dumps({
                    "type": type,
                    "relationships": filtered_relations,
                    "count": len(filtered_relations)
                }, indent=2)
            }
        
        @self.server.resource("memory://recent-activity")
        async def get_recent_activity() -> Dict[str, Any]:
            """Show recent memory system activity"""
            # Get full graph
            result = await self._call_external_api("/memory/graph", method="GET")
            
            if "error" in result:
                return {"error": result["error"]}
            
            # Sort entities by updated_at
            entities = result.get("entities", [])
            sorted_entities = sorted(
                entities,
                key=lambda e: e.get("updated_at", e.get("created_at", "")),
                reverse=True
            )[:20]  # Last 20 entities
            
            # Sort relations by created_at
            relations = result.get("relations", [])
            sorted_relations = sorted(
                relations,
                key=lambda r: r.get("created_at", ""),
                reverse=True
            )[:20]  # Last 20 relations
            
            return {
                "mimeType": "application/json",
                "text": json.dumps({
                    "recent_entities": sorted_entities,
                    "recent_relations": sorted_relations
                }, indent=2)
            }
    
    def setup_prompts(self):
        """Setup MCP prompts for memory-aware templates"""
        
        @self.server.prompt("extract-entities")
        async def extract_entities_prompt(text: str, focus_areas: Optional[List[str]] = None) -> str:
            """Prompt template for extracting entities from text"""
            focus_str = ""
            if focus_areas:
                focus_str = f"\nFocus particularly on: {', '.join(focus_areas)}"
            
            return f"""Extract entities from the following text. Identify people, projects, skills, events, and other notable entities.{focus_str}

Text to analyze:
{text}

For each entity found, provide:
1. Entity name
2. Entity type (person, project, skill, event, company, etc.)
3. Key observations about the entity
4. Any relationships mentioned

Format your response as a structured list that can be easily parsed."""
        
        @self.server.prompt("relationship-analysis")
        async def relationship_analysis_prompt(
            entity1: str, 
            entity2: str, 
            context: Optional[str] = None
        ) -> str:
            """Prompt template for analyzing relationships between entities"""
            context_str = ""
            if context:
                context_str = f"\n\nAdditional context: {context}"
            
            return f"""Analyze the relationship between these two entities:
- Entity 1: {entity1}
- Entity 2: {entity2}{context_str}

Consider:
1. What type of relationship exists? (works_with, manages, knows, uses, etc.)
2. What is the strength or importance of this relationship?
3. Are there any indirect connections through other entities?
4. What observations support this relationship?

Provide a detailed analysis of their connection."""
        
        @self.server.prompt("skill-assessment")
        async def skill_assessment_prompt(person: str, skill_area: str) -> str:
            """Prompt template for evaluating skill levels from observations"""
            return f"""Assess the skill level of {person} in the area of {skill_area}.

Based on available observations, evaluate:
1. Current proficiency level (beginner, intermediate, advanced, expert)
2. Specific evidence demonstrating this skill
3. Related skills or knowledge areas
4. Recommendations for skill development
5. How this skill has been applied in projects or work

Provide a comprehensive skill assessment with supporting evidence."""
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as streams:
            await self.server.run(
                streams.read_stream,
                streams.write_stream,
                self.server.create_initialization_options()
            )

def main():
    """Main entry point"""
    # Get configuration from environment
    external_api_url = os.getenv("MEMORY_EXTERNAL_API_URL", "https://localhost:8443")
    
    # Create and run server
    server = MemoryMCPServer(external_api_url)
    asyncio.run(server.run())

if __name__ == "__main__":
    main()