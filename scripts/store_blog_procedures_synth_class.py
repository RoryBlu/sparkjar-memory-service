#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Store comprehensive blog writing procedures for synth_class 24.
This script creates the complete blog writing knowledge base at the synth_class level.
"""
import asyncio
import os
import sys
from uuid import UUID, uuid4
from datetime import datetime
import argparse

# Add parent directory to path

from database import get_db
from services.memory_manager_hierarchical import HierarchicalMemoryManager
from services.embeddings import EmbeddingService
from sparkjar_crew.shared.schemas.memory_schemas import EntityCreate, ObservationCreate, RelationCreate
from config import settings

async def store_blog_writing_knowledge(client_id: UUID, synth_class_id: int = 24):
    """Store comprehensive blog writing knowledge base for synth_class 24"""
    
    # Get database session
    db = next(get_db())
    
    # Initialize services
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    
    manager = HierarchicalMemoryManager(db, embedding_service)
    
    logger.info(f"🚀 Storing blog writing knowledge for synth_class {synth_class_id}")
    logger.info(f"   Client ID: {client_id}")
    logger.info(f"   Actor Type: synth_class")
    logger.info(f"   Actor ID: {synth_class_id}")
    
    # Store all entities first, then create relationships
    entity_ids = {}
    
    # 1. Main Blog Writing SOP
    blog_sop = EntityCreate(
        name="Blog Writing Standard Operating Procedure",
        entityType="procedure_template",
        metadata={
            "procedure_type": "blog_writing",
            "version": "4.0",
            "synth_class": synth_class_id,
            "phases": [
                "Research & Planning",
                "Content Creation", 
                "Optimization & Enhancement",
                "Quality Assurance"
            ],
            "total_duration": "3-4 hours",
            "prerequisites": [
                "Understanding of target audience",
                "Access to keyword research tools",
                "Basic SEO knowledge",
                "Writing proficiency"
            ],
            "deliverables": [
                "1500-2500 word blog post",
                "SEO-optimized content",
                "Quality score ≥85%",
                "Publication-ready article"
            ]
        },
        observations=[
            ObservationCreate(
                type="procedure_phase",
                value={
                    "phase": 1,
                    "name": "Research & Planning",
                    "duration": "45-60 minutes",
                    "objectives": [
                        "Understand search intent",
                        "Identify content gaps",
                        "Define unique angle",
                        "Create detailed outline"
                    ],
                    "steps": [
                        {
                            "step": "1.1",
                            "action": "Topic Analysis",
                            "description": "Analyze topic viability and search potential",
                            "tools": ["Keyword research tool", "SERP analyzer", "Competitor analysis"]
                        },
                        {
                            "step": "1.2",
                            "action": "Audience Research",
                            "description": "Define reader persona and pain points",
                            "tools": ["Persona templates", "Survey data", "Analytics"]
                        },
                        {
                            "step": "1.3",
                            "action": "Content Planning",
                            "description": "Create hierarchical outline with word counts",
                            "tools": ["Outline template", "Content planner"]
                        }
                    ],
                    "deliverables": [
                        "Keyword research document",
                        "Audience persona profile",
                        "Detailed content outline",
                        "Success metrics defined"
                    ],
                    "quality_criteria": {
                        "keyword_relevance": "Primary keyword with 1000+ monthly searches",
                        "competition_analysis": "Identified 3+ content gaps",
                        "outline_completeness": "H2/H3 structure with 5+ sections"
                    }
                },
                source="synth_class_24_knowledge_base"
            ),
            ObservationCreate(
                type="procedure_phase",
                value={
                    "phase": 2,
                    "name": "Content Creation",
                    "duration": "90-120 minutes",
                    "objectives": [
                        "Write engaging introduction",
                        "Develop comprehensive body content",
                        "Craft compelling conclusion",
                        "Maintain consistent voice"
                    ],
                    "steps": [
                        {
                            "step": "2.1",
                            "action": "Introduction Writing",
                            "description": "Hook reader with compelling opening",
                            "tools": ["Hook templates", "Introduction formulas"]
                        },
                        {
                            "step": "2.2",
                            "action": "Body Development",
                            "description": "Write main content sections with evidence",
                            "tools": ["Paragraph templates", "Transition phrases"]
                        },
                        {
                            "step": "2.3",
                            "action": "Conclusion Crafting",
                            "description": "Summarize value and include CTA",
                            "tools": ["CTA templates", "Summary formulas"]
                        }
                    ],
                    "deliverables": [
                        "Complete first draft",
                        "All sections written",
                        "Evidence and examples included",
                        "CTAs integrated"
                    ],
                    "quality_criteria": {
                        "word_count": "1500-2500 words",
                        "paragraph_structure": "2-4 sentences per paragraph",
                        "evidence_inclusion": "Data/examples every 300 words",
                        "readability": "8th-9th grade level"
                    }
                },
                source="synth_class_24_knowledge_base"
            ),
            ObservationCreate(
                type="procedure_phase",
                value={
                    "phase": 3,
                    "name": "Optimization & Enhancement",
                    "duration": "30-45 minutes",
                    "objectives": [
                        "Optimize for search engines",
                        "Enhance readability",
                        "Add visual elements",
                        "Improve engagement"
                    ],
                    "steps": [
                        {
                            "step": "3.1",
                            "action": "SEO Optimization",
                            "description": "Optimize all on-page SEO elements",
                            "tools": ["SEO checklist", "Keyword density analyzer"]
                        },
                        {
                            "step": "3.2",
                            "action": "Readability Enhancement",
                            "description": "Improve sentence structure and flow",
                            "tools": ["Readability scorer", "Grammar checker"]
                        },
                        {
                            "step": "3.3",
                            "action": "Visual Enhancement",
                            "description": "Add images and formatting",
                            "tools": ["Image editor", "Formatting guide"]
                        }
                    ],
                    "deliverables": [
                        "SEO-optimized content",
                        "Enhanced readability",
                        "Visual elements added",
                        "Internal/external links"
                    ],
                    "quality_criteria": {
                        "keyword_density": "1-2% for primary keyword",
                        "flesch_score": "60-70 reading ease",
                        "image_frequency": "1 per 300-400 words",
                        "link_count": "3-5 internal, 2-3 external"
                    }
                },
                source="synth_class_24_knowledge_base"
            ),
            ObservationCreate(
                type="procedure_phase",
                value={
                    "phase": 4,
                    "name": "Quality Assurance",
                    "duration": "20-30 minutes",
                    "objectives": [
                        "Verify content accuracy",
                        "Check technical elements",
                        "Ensure quality standards",
                        "Prepare for publication"
                    ],
                    "steps": [
                        {
                            "step": "4.1",
                            "action": "Content Review",
                            "description": "Check accuracy, value, and completeness",
                            "tools": ["Quality checklist", "Fact checker"]
                        },
                        {
                            "step": "4.2",
                            "action": "Technical Review",
                            "description": "Verify all technical elements work",
                            "tools": ["Link checker", "Mobile preview"]
                        },
                        {
                            "step": "4.3",
                            "action": "Final Scoring",
                            "description": "Calculate quality scores",
                            "tools": ["Scoring rubric", "Quality calculator"]
                        }
                    ],
                    "deliverables": [
                        "Quality assessment report",
                        "All checks passed",
                        "Publication approval",
                        "Performance predictions"
                    ],
                    "quality_criteria": {
                        "content_quality": "≥90% score",
                        "seo_optimization": "≥85% score",
                        "user_experience": "≥90% score",
                        "overall_score": "≥85% minimum"
                    }
                },
                source="synth_class_24_knowledge_base"
            )
        ]
    )
    
    # Store the main SOP
    try:
        result = await manager.create_entities(
            client_id=client_id,
            actor_type='synth_class',
            actor_id=str(synth_class_id),
            entities=[blog_sop]
        )
        entity_ids['blog_sop'] = UUID(result[0]['id'])
        logger.info(f"✅ Created Blog SOP with ID: {entity_ids['blog_sop']}")
    except Exception as e:
        logger.error(f"❌ Error creating Blog SOP: {e}")
        db.close()
        return
    
    # 2. Blog Structure Template
    blog_structure = EntityCreate(
        name="Blog Post Structure Template",
        entityType="content_structure",
        metadata={
            "structure_type": "standard_blog_post",
            "synth_class": synth_class_id,
            "version": "2.0",
            "optimal_length": "1500-2500 words",
            "sections": [
                "Title & Meta",
                "Introduction",
                "Body (3-5 sections)",
                "Conclusion",
                "Technical Elements"
            ]
        },
        observations=[
            ObservationCreate(
                type="content_structure",
                value={
                    "structure_type": "blog_sections",
                    "sections": [
                        {
                            "name": "Title & Meta",
                            "purpose": "Attract clicks and optimize for search",
                            "word_count_target": 0,
                            "key_elements": [
                                "Title (50-60 chars)",
                                "Meta description (150-160 chars)",
                                "URL slug",
                                "Focus keyword inclusion"
                            ]
                        },
                        {
                            "name": "Introduction",
                            "purpose": "Hook reader and preview value",
                            "word_count_target": 150,
                            "key_elements": [
                                "Attention-grabbing hook",
                                "Problem/context statement",
                                "Thesis/main point",
                                "Value preview"
                            ]
                        },
                        {
                            "name": "Body Section",
                            "purpose": "Deliver main value and information",
                            "word_count_target": 400,
                            "key_elements": [
                                "H2 heading with keyword",
                                "Topic sentence",
                                "Supporting evidence",
                                "Examples/data",
                                "Transition to next"
                            ]
                        },
                        {
                            "name": "Conclusion",
                            "purpose": "Reinforce value and drive action",
                            "word_count_target": 150,
                            "key_elements": [
                                "Key points summary",
                                "Main takeaway",
                                "Clear CTA",
                                "Next steps"
                            ]
                        }
                    ],
                    "flow_pattern": "Problem → Solution → Implementation → Results",
                    "engagement_hooks": [
                        "Questions to maintain curiosity",
                        "Stories and examples",
                        "Data and statistics",
                        "Visual breaks every 300 words",
                        "Subheadings for scanning"
                    ]
                },
                source="synth_class_24_knowledge_base"
            )
        ]
    )
    
    # Store structure template
    try:
        result = await manager.create_entities(
            client_id=client_id,
            actor_type='synth_class',
            actor_id=str(synth_class_id),
            entities=[blog_structure]
        )
        entity_ids['blog_structure'] = UUID(result[0]['id'])
        logger.info(f"✅ Created Blog Structure with ID: {entity_ids['blog_structure']}")
    except Exception as e:
        logger.error(f"❌ Error creating Blog Structure: {e}")
    
    # 3. Quality Assurance Checklist
    qa_checklist = EntityCreate(
        name="Blog Quality Assurance Checklist",
        entityType="checklist_template",
        metadata={
            "checklist_type": "quality_assurance",
            "version": "3.0",
            "synth_class": synth_class_id,
            "categories": [
                {"name": "Content Quality", "weight": 0.4, "required_score": 0.9},
                {"name": "SEO Optimization", "weight": 0.3, "required_score": 0.85},
                {"name": "User Experience", "weight": 0.2, "required_score": 0.9},
                {"name": "Technical Performance", "weight": 0.1, "required_score": 0.8}
            ],
            "passing_score": 0.85,
            "related_procedure": str(entity_ids['blog_sop'])
        },
        observations=[
            ObservationCreate(
                type="quality_assessment",
                value={
                    "assessment_type": "content_quality_criteria",
                    "criteria": {
                        "unique_value": {
                            "description": "Provides insights not found elsewhere",
                            "weight": 0.3,
                            "required": True
                        },
                        "search_intent_match": {
                            "description": "Fully answers user's query",
                            "weight": 0.3,
                            "required": True
                        },
                        "actionable_advice": {
                            "description": "Includes practical takeaways",
                            "weight": 0.2,
                            "required": True
                        },
                        "evidence_based": {
                            "description": "Claims supported by data/examples",
                            "weight": 0.1,
                            "required": False
                        },
                        "comprehensive_coverage": {
                            "description": "Covers topic thoroughly",
                            "weight": 0.1,
                            "required": False
                        }
                    },
                    "scoring_method": "weighted_average",
                    "minimum_score": 0.9
                },
                source="synth_class_24_knowledge_base"
            ),
            ObservationCreate(
                type="quality_assessment",
                value={
                    "assessment_type": "seo_optimization_criteria",
                    "criteria": {
                        "title_optimization": {
                            "description": "Title tag 50-60 chars with keyword",
                            "weight": 0.25,
                            "required": True
                        },
                        "meta_description": {
                            "description": "Compelling meta 150-160 chars",
                            "weight": 0.25,
                            "required": True
                        },
                        "header_structure": {
                            "description": "Proper H1→H2→H3 hierarchy",
                            "weight": 0.2,
                            "required": True
                        },
                        "keyword_usage": {
                            "description": "Natural keyword integration 1-2%",
                            "weight": 0.15,
                            "required": True
                        },
                        "internal_linking": {
                            "description": "3-5 relevant internal links",
                            "weight": 0.1,
                            "required": False
                        },
                        "image_optimization": {
                            "description": "Alt text and compression",
                            "weight": 0.05,
                            "required": False
                        }
                    },
                    "scoring_method": "weighted_average",
                    "minimum_score": 0.85
                },
                source="synth_class_24_knowledge_base"
            )
        ]
    )
    
    # Store QA checklist
    try:
        result = await manager.create_entities(
            client_id=client_id,
            actor_type='synth_class',
            actor_id=str(synth_class_id),
            entities=[qa_checklist]
        )
        entity_ids['qa_checklist'] = UUID(result[0]['id'])
        logger.info(f"✅ Created QA Checklist with ID: {entity_ids['qa_checklist']}")
    except Exception as e:
        logger.error(f"❌ Error creating QA Checklist: {e}")
    
    # 4. Writing Style Guide
    style_guide = EntityCreate(
        name="Blog Writing Style Guide",
        entityType="style_guide",
        metadata={
            "guide_type": "writing",
            "synth_class": synth_class_id,
            "voice": "Professional yet conversational",
            "tone_variations": {
                "educational": "Clear, patient, thorough",
                "inspirational": "Uplifting, motivating, empowering",
                "analytical": "Data-driven, objective, logical",
                "practical": "Action-oriented, pragmatic, direct"
            },
            "principles": [
                {"name": "Clarity First", "description": "Simple language for complex ideas"},
                {"name": "Value Dense", "description": "Every paragraph adds value"},
                {"name": "Action-Oriented", "description": "Include practical takeaways"},
                {"name": "Evidence-Based", "description": "Support claims with data"},
                {"name": "Reader-Centric", "description": "Focus on reader benefits"}
            ]
        },
        observations=[
            ObservationCreate(
                type="writing_technique",
                value={
                    "technique_type": "engagement_hooks",
                    "category": "engagement",
                    "description": "Techniques to capture and maintain reader attention",
                    "examples": [
                        "Question hook: 'Have you ever wondered why...'",
                        "Statistic hook: '73% of marketers struggle with...'",
                        "Story hook: 'Last Tuesday, everything changed when...'",
                        "Problem hook: 'Most people waste hours trying to...'",
                        "Quote hook: 'As Einstein once said...'"
                    ],
                    "when_to_use": "Opening paragraphs, section transitions, re-engagement points",
                    "effectiveness_rating": 4.5
                },
                source="synth_class_24_knowledge_base"
            ),
            ObservationCreate(
                type="writing_technique",
                value={
                    "technique_type": "paragraph_structure",
                    "category": "clarity",
                    "description": "PEEL method for clear paragraphs",
                    "examples": [
                        "Point: State your main idea",
                        "Evidence: Provide supporting data/examples",
                        "Explanation: Explain why it matters",
                        "Link: Connect to next point"
                    ],
                    "when_to_use": "All body paragraphs for maximum clarity",
                    "effectiveness_rating": 4.8
                },
                source="synth_class_24_knowledge_base"
            ),
            ObservationCreate(
                type="writing_technique",
                value={
                    "technique_type": "transition_mastery",
                    "category": "flow",
                    "description": "Smooth transitions between ideas",
                    "examples": [
                        "Addition: 'Furthermore', 'Additionally', 'Moreover'",
                        "Contrast: 'However', 'On the other hand', 'Conversely'",
                        "Cause/Effect: 'Therefore', 'As a result', 'Consequently'",
                        "Example: 'For instance', 'To illustrate', 'Specifically'",
                        "Summary: 'In summary', 'To sum up', 'All things considered'"
                    ],
                    "when_to_use": "Between paragraphs and sections",
                    "effectiveness_rating": 4.3
                },
                source="synth_class_24_knowledge_base"
            )
        ]
    )
    
    # Store style guide
    try:
        result = await manager.create_entities(
            client_id=client_id,
            actor_type='synth_class',
            actor_id=str(synth_class_id),
            entities=[style_guide]
        )
        entity_ids['style_guide'] = UUID(result[0]['id'])
        logger.info(f"✅ Created Style Guide with ID: {entity_ids['style_guide']}")
    except Exception as e:
        logger.error(f"❌ Error creating Style Guide: {e}")
    
    # 5. SEO Best Practices
    seo_practices = EntityCreate(
        name="Blog SEO Best Practices",
        entityType="procedure_template",
        metadata={
            "procedure_type": "seo_optimization",
            "version": "2.0",
            "synth_class": synth_class_id,
            "prerequisites": ["Keyword research completed", "Content draft ready"],
            "deliverables": ["Fully optimized blog post", "Meta tags configured"]
        },
        observations=[
            ObservationCreate(
                type="writing_technique",
                value={
                    "technique_type": "keyword_integration",
                    "category": "seo",
                    "description": "Natural keyword placement strategies",
                    "examples": [
                        "Title: Include primary keyword near beginning",
                        "First paragraph: Use primary keyword within first 100 words",
                        "Headers: Include in 1-2 H2 tags naturally",
                        "Body: Maintain 1-2% density with variations",
                        "Meta: Include in meta description naturally",
                        "URL: Use primary keyword in slug"
                    ],
                    "when_to_use": "During optimization phase",
                    "effectiveness_rating": 4.7
                },
                source="synth_class_24_knowledge_base"
            ),
            ObservationCreate(
                type="writing_technique",
                value={
                    "technique_type": "semantic_seo",
                    "category": "seo",
                    "description": "Topic modeling and entity optimization",
                    "examples": [
                        "Use LSI keywords throughout",
                        "Cover related subtopics comprehensively",
                        "Include entities and their relationships",
                        "Answer 'People Also Ask' questions",
                        "Create topic clusters with internal links"
                    ],
                    "when_to_use": "Content planning and writing phases",
                    "effectiveness_rating": 4.6
                },
                source="synth_class_24_knowledge_base"
            )
        ]
    )
    
    # Store SEO practices
    try:
        result = await manager.create_entities(
            client_id=client_id,
            actor_type='synth_class',
            actor_id=str(synth_class_id),
            entities=[seo_practices]
        )
        entity_ids['seo_practices'] = UUID(result[0]['id'])
        logger.info(f"✅ Created SEO Practices with ID: {entity_ids['seo_practices']}")
    except Exception as e:
        logger.error(f"❌ Error creating SEO Practices: {e}")
    
    logger.info("\n📊 Summary of created entities:")
    for name, id in entity_ids.items():
        logger.info(f"  - {name}: {id}")
    
    logger.info(f"\n⚡ Blog writing knowledge base successfully stored for synth_class {synth_class_id}")
    logger.info("   All synths inheriting from this class can now access this knowledge!")
    
    # Note about relationships
    logger.info("\n📝 Note: Relationships between entities cannot be created at synth_class level")
    logger.info("   due to system constraints. Synths will create relationships when using these templates.")
    
    # Close database connection
    db.close()

async def verify_blog_knowledge(client_id: UUID, synth_id: UUID, synth_class_id: int = 24):
    """Verify that a synth can access the blog writing knowledge through hierarchy"""
    
    # Get database session
    db = next(get_db())
    
    # Initialize services
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    
    manager = HierarchicalMemoryManager(db, embedding_service)
    
    logger.info(f"\n🔍 Verifying blog knowledge access for synth {synth_id}")
    
    # Test queries
    test_queries = [
        "blog writing procedure",
        "quality checklist",
        "writing style guide",
        "SEO best practices",
        "content structure"
    ]
    
    for query in test_queries:
        logger.info(f"\n📌 Testing query: '{query}'")
        
        # Search without hierarchy (should find nothing)
        strict_results = await manager.search_nodes(
            client_id=client_id,
            actor_type='synth',
            actor_id=synth_id,
            query=query,
            include_hierarchy=False
        )
        
        logger.info(f"  Strict search: {len(strict_results)} results")
        
        # Search with hierarchy (should find templates)
        hierarchical_results = await manager.search_hierarchical_memories(
            client_id=client_id,
            actor_type='synth',
            actor_id=synth_id,
            query=query,
            include_synth_class=True
        )
        
        logger.info(f"  Hierarchical search: {len(hierarchical_results)} results")
        for result in hierarchical_results[:3]:  # Show first 3
            logger.info(f"    - {result['entity_name']} (from {result['access_source']})")
    
    db.close()

# Main execution
async def main():
    """Main function with argument parsing"""
    
    parser = argparse.ArgumentParser(
        description="Store blog writing knowledge for synth_class 24"
    )
    parser.add_argument(
        "--client-id", 
        type=str, 
        required=True, 
        help="Client UUID"
    )
    parser.add_argument(
        "--synth-id", 
        type=str, 
        help="Synth UUID for verification"
    )
    parser.add_argument(
        "--synth-class-id", 
        type=int, 
        default=24, 
        help="Synth class ID (default: 24)"
    )
    parser.add_argument(
        "--verify-only", 
        action="store_true", 
        help="Only verify access, don't store"
    )
    
    args = parser.parse_args()
    
    client_id = UUID(args.client_id)
    synth_class_id = args.synth_class_id
    
    if args.verify_only:
        if not args.synth_id:
            logger.info("❌ --synth-id required for verification")
            return
        synth_id = UUID(args.synth_id)
        await verify_blog_knowledge(client_id, synth_id, synth_class_id)
    else:
        # Store the knowledge base
        await store_blog_writing_knowledge(client_id, synth_class_id)
        
        # Optionally verify
        if args.synth_id:
            synth_id = UUID(args.synth_id)
            await verify_blog_knowledge(client_id, synth_id, synth_class_id)

if __name__ == "__main__":
    asyncio.run(main())