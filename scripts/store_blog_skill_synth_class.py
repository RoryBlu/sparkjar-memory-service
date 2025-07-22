#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Store blog writing skill for synth_class 24.
This creates the foundational blog writing knowledge at the synth_class level.

Key concepts:
- NO client_id needed for synth_class memories
- synth_class 24 is the ROOT ENTITY
- All procedures, guides, etc. are authored by synth_class 24
- Relationships connect everything back to synth_class 24
"""
import asyncio
import os
import sys
from uuid import UUID, uuid4
from datetime import datetime, timedelta

# Add parent directory to path

from database import get_db
from services.memory_manager import MemoryManager
from services.embeddings import EmbeddingService
from sparkjar_crew.shared.schemas.memory_schemas import EntityCreate, ObservationCreate, RelationCreate
from config import settings

async def store_blog_writing_skill():
    """Store blog writing skill for synth_class 24"""
    
    # Get database session
    db = next(get_db())
    
    # Initialize services
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    
    manager = MemoryManager(db, embedding_service)
    
    # Constants - NO CLIENT_ID!
    ACTOR_TYPE = 'synth_class'
    ACTOR_ID = '24'
    
    logger.info(f"🚀 Storing blog writing skill")
    logger.info(f"   Actor Type: {ACTOR_TYPE}")
    logger.info(f"   Actor ID: {ACTOR_ID}")
    logger.info(f"   Client ID: None (not needed for synth_class)")
    
    # Track all entity IDs for relationships
    entity_ids = {}
    
    # =============================
    # 1. CREATE SYNTH_CLASS 24 ENTITY
    # =============================
    synth_class_entity = EntityCreate(
        name="Blog Writer Class",
        entityType="synth_class",
        metadata={
            "class_id": 24,
            "specialization": "Content Creation",
            "capabilities": [
                "Blog Writing",
                "SEO Optimization",
                "Content Strategy",
                "Quality Assurance"
            ],
            "version": "1.0",
            "created_date": datetime.utcnow().isoformat()
        },
        observations=[
            ObservationCreate(
                type="class_description",
                value={
                    "purpose": "Professional blog content creation",
                    "skills": [
                        "Research and planning",
                        "Engaging writing",
                        "SEO optimization",
                        "Quality control"
                    ],
                    "output_types": [
                        "Blog posts",
                        "Articles",
                        "Guides",
                        "Tutorials"
                    ],
                    "quality_standards": {
                        "minimum_score": 85,
                        "word_count_range": "1500-2500",
                        "readability_target": "8th-9th grade"
                    }
                },
                source="class_definition"
            )
        ]
    )
    
    # Store synth_class entity - NO CLIENT_ID!
    try:
        # For synth_class, we bypass client_id requirement
        # This is a direct database operation since MemoryManager expects client_id
        from sqlalchemy.orm import Session
        from sparkjar_crew.shared.schemas.memory_schemas import Entity as EntityModel
        
        entity_data = synth_class_entity.dict()
        entity_id = uuid4()
        
        # Create entity directly
        db_entity = EntityModel(
            id=entity_id,
            client_id=None,  # No client for synth_class
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_name=entity_data['name'],
            entity_type=entity_data['entityType'],
            metadata=entity_data.get('metadata', {}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_entity)
        db.commit()
        
        entity_ids['synth_class'] = entity_id
        logger.info(f"✅ Created Synth Class 24 with ID: {entity_ids['synth_class']}")
    except Exception as e:
        logger.error(f"❌ Error creating Synth Class: {e}")
        db.close()
        return
    
    # =============================
    # 2. BLOG WRITING SOP (authored by synth_class 24)
    # =============================
    blog_sop = EntityCreate(
        name="Blog Writing Standard Operating Procedure",
        entityType="procedure",
        metadata={
            "procedure_type": "standard_operating_procedure",
            "domain": "blog_writing",
            "version": "4.0",
            "total_phases": 4,
            "estimated_duration": "3-4 hours",
            "effectiveness_score": 0.92,
            "usage_count": 0,
            "last_updated": datetime.utcnow().isoformat()
        },
        observations=[
            ObservationCreate(
                type="procedure_overview",
                value={
                    "description": "Comprehensive 4-phase blog writing process",
                    "phases": [
                        {
                            "number": 1,
                            "name": "Research & Planning",
                            "duration": "45-60 minutes",
                            "deliverables": ["Keyword research", "Audience profile", "Content outline"]
                        },
                        {
                            "number": 2,
                            "name": "Content Creation",
                            "duration": "90-120 minutes",
                            "deliverables": ["Complete draft", "Engaging content", "Proper structure"]
                        },
                        {
                            "number": 3,
                            "name": "Optimization & Enhancement",
                            "duration": "30-45 minutes",
                            "deliverables": ["SEO optimization", "Readability improvements", "Visual elements"]
                        },
                        {
                            "number": 4,
                            "name": "Quality Assurance",
                            "duration": "20-30 minutes",
                            "deliverables": ["Quality report", "Publication approval"]
                        }
                    ],
                    "success_criteria": {
                        "quality_score": "≥85%",
                        "seo_score": "≥80%",
                        "readability": "Flesch 60-70"
                    }
                },
                source="synth_class_24"
            ),
            ObservationCreate(
                type="phase_1_details",
                value={
                    "phase": "Research & Planning",
                    "steps": [
                        {
                            "step": 1,
                            "action": "Keyword Research",
                            "details": "Identify primary and secondary keywords with search volume >1000",
                            "tools": ["SEMrush", "Ahrefs", "Google Keyword Planner"],
                            "output": "Keyword strategy document"
                        },
                        {
                            "step": 2,
                            "action": "SERP Analysis",
                            "details": "Analyze top 10 results for content gaps and opportunities",
                            "criteria": ["Content depth", "Missing topics", "User intent match"],
                            "output": "Competitive analysis"
                        },
                        {
                            "step": 3,
                            "action": "Audience Profiling",
                            "details": "Define reader persona, pain points, and knowledge level",
                            "components": ["Demographics", "Challenges", "Goals", "Objections"],
                            "output": "Audience persona document"
                        },
                        {
                            "step": 4,
                            "action": "Content Outlining",
                            "details": "Create hierarchical structure with word count allocation",
                            "structure": ["H1 title", "H2 sections (3-5)", "H3 subsections", "CTAs"],
                            "output": "Detailed content outline"
                        }
                    ],
                    "quality_gates": [
                        "Primary keyword difficulty <70",
                        "At least 3 content gaps identified",
                        "Clear unique angle defined"
                    ]
                },
                source="synth_class_24"
            ),
            ObservationCreate(
                type="phase_2_details",
                value={
                    "phase": "Content Creation",
                    "writing_formula": {
                        "introduction": {
                            "components": ["Hook", "Context", "Thesis", "Preview"],
                            "word_count": 150,
                            "hook_types": ["Question", "Statistic", "Story", "Problem", "Quote"]
                        },
                        "body_sections": {
                            "structure": "PEEL",
                            "components": ["Point", "Evidence", "Explanation", "Link"],
                            "word_count_per_section": 300-500,
                            "evidence_types": ["Data", "Examples", "Expert quotes", "Case studies"]
                        },
                        "conclusion": {
                            "components": ["Summary", "Implications", "CTA", "Next steps"],
                            "word_count": 150,
                            "cta_types": ["Subscribe", "Download", "Try", "Share"]
                        }
                    },
                    "writing_principles": [
                        "Use 'you' and direct address",
                        "One idea per paragraph",
                        "Active voice >80%",
                        "Vary sentence length",
                        "Include specific examples"
                    ],
                    "engagement_techniques": [
                        "Ask rhetorical questions",
                        "Use analogies and metaphors",
                        "Include surprising statistics",
                        "Tell mini-stories",
                        "Create knowledge gaps"
                    ]
                },
                source="synth_class_24"
            ),
            ObservationCreate(
                type="phase_3_details",
                value={
                    "phase": "Optimization & Enhancement",
                    "seo_checklist": [
                        {
                            "element": "Title Tag",
                            "requirement": "50-60 chars, keyword near front",
                            "priority": "critical"
                        },
                        {
                            "element": "Meta Description",
                            "requirement": "150-160 chars, compelling CTA",
                            "priority": "critical"
                        },
                        {
                            "element": "URL Slug",
                            "requirement": "Short, keyword-focused, hyphens",
                            "priority": "high"
                        },
                        {
                            "element": "Header Tags",
                            "requirement": "H1→H2→H3 hierarchy, keywords in H2s",
                            "priority": "high"
                        },
                        {
                            "element": "Keyword Density",
                            "requirement": "1-2% primary, LSI throughout",
                            "priority": "medium"
                        },
                        {
                            "element": "Internal Links",
                            "requirement": "3-5 relevant pages",
                            "priority": "medium"
                        },
                        {
                            "element": "Image Alt Text",
                            "requirement": "Descriptive, keyword-inclusive",
                            "priority": "medium"
                        }
                    ],
                    "readability_targets": {
                        "flesch_reading_ease": 60-70,
                        "average_sentence_length": 15-20,
                        "paragraph_length": "2-4 sentences",
                        "subheading_frequency": "Every 300 words"
                    }
                },
                source="synth_class_24"
            ),
            ObservationCreate(
                type="phase_4_details",
                value={
                    "phase": "Quality Assurance",
                    "quality_dimensions": {
                        "content_quality": {
                            "weight": 0.4,
                            "criteria": [
                                "Unique value provided",
                                "Search intent satisfied",
                                "Actionable advice included",
                                "Claims evidence-based",
                                "Comprehensive coverage"
                            ]
                        },
                        "seo_optimization": {
                            "weight": 0.3,
                            "criteria": [
                                "All meta elements optimized",
                                "Keyword placement natural",
                                "Link profile balanced",
                                "Technical SEO clean"
                            ]
                        },
                        "user_experience": {
                            "weight": 0.2,
                            "criteria": [
                                "Scannable formatting",
                                "Mobile-friendly",
                                "Fast load time",
                                "Clear navigation"
                            ]
                        },
                        "technical_quality": {
                            "weight": 0.1,
                            "criteria": [
                                "No broken links",
                                "Images optimized",
                                "Schema markup present",
                                "No errors"
                            ]
                        }
                    },
                    "minimum_scores": {
                        "overall": 0.85,
                        "content": 0.90,
                        "seo": 0.80,
                        "ux": 0.85
                    },
                    "review_checklist": [
                        "Read entire post aloud",
                        "Check all facts and data",
                        "Verify all links work",
                        "Test mobile display",
                        "Run grammar check",
                        "Calculate quality score"
                    ]
                },
                source="synth_class_24"
            )
        ]
    )
    
    # Store Blog SOP
    try:
        result = await manager.create_entities(
            client_id=None,
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entities=[blog_sop]
        )
        entity_ids['blog_sop'] = UUID(result[0]['id'])
        logger.info(f"✅ Created Blog SOP with ID: {entity_ids['blog_sop']}")
    except Exception as e:
        logger.error(f"❌ Error creating Blog SOP: {e}")
    
    # =============================
    # 3. QUALITY CHECKLIST
    # =============================
    quality_checklist = EntityCreate(
        name="Blog Quality Assurance Checklist",
        entityType="checklist",
        metadata={
            "checklist_type": "quality_assurance",
            "version": "3.0",
            "total_items": 25,
            "categories": 4,
            "passing_threshold": 0.85,
            "related_procedure": "Blog Writing Standard Operating Procedure"
        },
        observations=[
            ObservationCreate(
                type="checklist_category",
                value={
                    "category": "Content Quality",
                    "weight": 0.4,
                    "items": [
                        {
                            "item": "Provides unique value not found elsewhere",
                            "required": True,
                            "verification": "Compare to top 5 SERP results"
                        },
                        {
                            "item": "Fully answers the search intent",
                            "required": True,
                            "verification": "Maps to user query types"
                        },
                        {
                            "item": "Includes specific, actionable advice",
                            "required": True,
                            "verification": "Count actionable tips"
                        },
                        {
                            "item": "Uses recent data and examples",
                            "required": False,
                            "verification": "Check dates within 2 years"
                        },
                        {
                            "item": "Free of fluff and filler content",
                            "required": True,
                            "verification": "Every paragraph adds value"
                        }
                    ]
                },
                source="synth_class_24"
            ),
            ObservationCreate(
                type="checklist_category",
                value={
                    "category": "SEO Optimization",
                    "weight": 0.3,
                    "items": [
                        {
                            "item": "Title tag optimized (50-60 characters)",
                            "required": True,
                            "verification": "Character count and keyword placement"
                        },
                        {
                            "item": "Meta description compelling (150-160 chars)",
                            "required": True,
                            "verification": "Includes CTA and keyword"
                        },
                        {
                            "item": "Headers properly structured (H1→H2→H3)",
                            "required": True,
                            "verification": "Check HTML hierarchy"
                        },
                        {
                            "item": "Keyword density appropriate (1-2%)",
                            "required": True,
                            "verification": "Calculate density"
                        },
                        {
                            "item": "Internal/external links balanced",
                            "required": False,
                            "verification": "3-5 internal, 2-3 external"
                        }
                    ]
                },
                source="synth_class_24"
            ),
            ObservationCreate(
                type="scoring_methodology",
                value={
                    "calculation": "weighted_average",
                    "scoring_scale": {
                        "0": "Not met",
                        "0.5": "Partially met",
                        "1": "Fully met"
                    },
                    "interpretation": {
                        "below_0.7": "Major revisions needed",
                        "0.7_to_0.85": "Minor improvements required",
                        "0.85_to_0.95": "Ready to publish",
                        "above_0.95": "Exceptional quality"
                    },
                    "reporting": {
                        "format": "percentage",
                        "breakdown": "by_category",
                        "recommendations": "auto_generated"
                    }
                },
                source="synth_class_24"
            )
        ]
    )
    
    # Store Quality Checklist
    try:
        result = await manager.create_entities(
            client_id=None,
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entities=[quality_checklist]
        )
        entity_ids['quality_checklist'] = UUID(result[0]['id'])
        logger.info(f"✅ Created Quality Checklist with ID: {entity_ids['quality_checklist']}")
    except Exception as e:
        logger.error(f"❌ Error creating Quality Checklist: {e}")
    
    # =============================
    # 4. WRITING STYLE GUIDE
    # =============================
    style_guide = EntityCreate(
        name="Blog Writing Style Guide",
        entityType="style_guide",
        metadata={
            "guide_type": "writing_style",
            "version": "2.0",
            "voice": "Professional yet conversational",
            "reading_level": "8th-9th grade",
            "perspective": "Second person (you)",
            "tone_variations": {
                "educational": "Clear, patient, thorough",
                "analytical": "Data-driven, objective",
                "inspirational": "Uplifting, empowering",
                "practical": "Direct, actionable"
            }
        },
        observations=[
            ObservationCreate(
                type="writing_principles",
                value={
                    "core_principles": [
                        {
                            "principle": "Clarity First",
                            "description": "Use simple language to explain complex ideas",
                            "examples": {
                                "good": "This tool helps you write better",
                                "bad": "This instrument facilitates enhanced composition"
                            }
                        },
                        {
                            "principle": "Value Dense",
                            "description": "Every paragraph must add value",
                            "examples": {
                                "good": "Here are 3 specific ways to improve",
                                "bad": "There are various methods one might consider"
                            }
                        },
                        {
                            "principle": "Action-Oriented",
                            "description": "Include practical takeaways",
                            "examples": {
                                "good": "Follow these 5 steps to implement",
                                "bad": "Implementation may vary"
                            }
                        }
                    ],
                    "sentence_guidelines": {
                        "average_length": "15-20 words",
                        "variety": "Mix short, medium, and long",
                        "active_voice": "80% minimum",
                        "personal_pronouns": "Use 'you' frequently"
                    },
                    "paragraph_guidelines": {
                        "length": "2-4 sentences",
                        "structure": "One main idea per paragraph",
                        "transitions": "Link each to the next",
                        "white_space": "Optimize for scanning"
                    }
                },
                source="synth_class_24"
            ),
            ObservationCreate(
                type="engagement_techniques",
                value={
                    "hooks": [
                        {
                            "type": "Question",
                            "when": "Opening, transitions",
                            "example": "Have you ever wondered why 90% of blogs fail?"
                        },
                        {
                            "type": "Statistic",
                            "when": "Support claims",
                            "example": "Studies show that 73% of readers scan, not read"
                        },
                        {
                            "type": "Story",
                            "when": "Illustrate concepts",
                            "example": "Last week, a client doubled traffic using this method"
                        }
                    ],
                    "maintaining_interest": [
                        "Use pattern interrupts",
                        "Vary content types (text, lists, quotes)",
                        "Include unexpected insights",
                        "Create open loops",
                        "Use conversational asides"
                    ],
                    "closing_strong": [
                        "Summarize key value",
                        "Paint vision of success",
                        "Give immediate next step",
                        "Create urgency",
                        "End with empowerment"
                    ]
                },
                source="synth_class_24"
            )
        ]
    )
    
    # Store Style Guide
    try:
        result = await manager.create_entities(
            client_id=None,
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entities=[style_guide]
        )
        entity_ids['style_guide'] = UUID(result[0]['id'])
        logger.info(f"✅ Created Style Guide with ID: {entity_ids['style_guide']}")
    except Exception as e:
        logger.error(f"❌ Error creating Style Guide: {e}")
    
    # =============================
    # 5. BLOG TEMPLATE STRUCTURE
    # =============================
    blog_template = EntityCreate(
        name="Blog Post Template Structure",
        entityType="template",
        metadata={
            "template_type": "blog_post",
            "version": "3.0",
            "format": "json_schema",
            "word_count_target": 2000,
            "sections": 7
        },
        observations=[
            ObservationCreate(
                type="template_structure",
                value={
                    "blog_post_schema": {
                        "title": {
                            "max_length": 60,
                            "include_keyword": True,
                            "format": "Sentence case"
                        },
                        "meta": {
                            "description": {
                                "length": "150-160",
                                "include_cta": True
                            },
                            "author": "synth_name",
                            "publish_date": "ISO 8601",
                            "categories": ["primary", "secondary"],
                            "tags": ["5-10 relevant tags"]
                        },
                        "content": {
                            "introduction": {
                                "hook": "required",
                                "thesis": "required",
                                "preview": "bullet points or paragraph"
                            },
                            "body": {
                                "sections": "3-5",
                                "structure": "H2 → paragraphs → H3 (optional)",
                                "media": "1 image per 300-400 words"
                            },
                            "conclusion": {
                                "summary": "key points",
                                "cta": "primary and secondary",
                                "next_steps": "clear actions"
                            }
                        },
                        "seo": {
                            "focus_keyword": "required",
                            "keyword_density": "1-2%",
                            "internal_links": "3-5",
                            "external_links": "2-3"
                        }
                    }
                },
                source="synth_class_24"
            )
        ]
    )
    
    # Store Blog Template
    try:
        result = await manager.create_entities(
            client_id=None,
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entities=[blog_template]
        )
        entity_ids['blog_template'] = UUID(result[0]['id'])
        logger.info(f"✅ Created Blog Template with ID: {entity_ids['blog_template']}")
    except Exception as e:
        logger.error(f"❌ Error creating Blog Template: {e}")
    
    # =============================
    # 6. PERFORMANCE TRACKING
    # =============================
    performance_metrics = EntityCreate(
        name="Blog Performance Metrics",
        entityType="metrics_framework",
        metadata={
            "framework_type": "performance_tracking",
            "version": "1.0",
            "tracking_period": "weekly",
            "kpis": [
                "Organic traffic",
                "Engagement rate",
                "Conversion rate",
                "Quality score"
            ]
        },
        observations=[
            ObservationCreate(
                type="metric_definitions",
                value={
                    "traffic_metrics": {
                        "organic_visitors": {
                            "source": "Google Analytics",
                            "target": ">500 in first week",
                            "growth": "20% week-over-week"
                        },
                        "page_views": {
                            "calculation": "unique + returning",
                            "target": ">750 in first week"
                        }
                    },
                    "engagement_metrics": {
                        "time_on_page": {
                            "target": ">3 minutes",
                            "indicates": "content value"
                        },
                        "scroll_depth": {
                            "target": ">75%",
                            "indicates": "full consumption"
                        },
                        "bounce_rate": {
                            "target": "<40%",
                            "indicates": "relevance"
                        }
                    },
                    "conversion_metrics": {
                        "cta_clicks": {
                            "target": ">5%",
                            "optimize": "CTA placement and copy"
                        },
                        "email_signups": {
                            "target": ">2%",
                            "optimize": "Value proposition"
                        }
                    },
                    "review_schedule": {
                        "week_1": "Initial performance check",
                        "week_4": "Full analysis and optimization",
                        "week_12": "Comprehensive review and update"
                    }
                },
                source="synth_class_24"
            )
        ]
    )
    
    # Store Performance Metrics
    try:
        result = await manager.create_entities(
            client_id=None,
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entities=[performance_metrics]
        )
        entity_ids['performance_metrics'] = UUID(result[0]['id'])
        logger.info(f"✅ Created Performance Metrics with ID: {entity_ids['performance_metrics']}")
    except Exception as e:
        logger.error(f"❌ Error creating Performance Metrics: {e}")
    
    # =============================
    # 7. CREATE RELATIONSHIPS
    # =============================
    logger.info("\n📊 Creating relationships between entities...")
    
    relationships = [
        {
            "from": "blog_sop",
            "to": "synth_class",
            "type": "authored_by",
            "metadata": {
                "creation_date": datetime.utcnow().isoformat(),
                "purpose": "Standard procedure for all blog writers"
            }
        },
        {
            "from": "quality_checklist",
            "to": "synth_class",
            "type": "authored_by",
            "metadata": {
                "creation_date": datetime.utcnow().isoformat(),
                "purpose": "Quality assurance for blog posts"
            }
        },
        {
            "from": "style_guide",
            "to": "synth_class",
            "type": "authored_by",
            "metadata": {
                "creation_date": datetime.utcnow().isoformat(),
                "purpose": "Writing style standards"
            }
        },
        {
            "from": "blog_template",
            "to": "synth_class",
            "type": "authored_by",
            "metadata": {
                "creation_date": datetime.utcnow().isoformat(),
                "purpose": "Standard blog structure"
            }
        },
        {
            "from": "performance_metrics",
            "to": "synth_class",
            "type": "authored_by",
            "metadata": {
                "creation_date": datetime.utcnow().isoformat(),
                "purpose": "Performance tracking framework"
            }
        },
        {
            "from": "quality_checklist",
            "to": "blog_sop",
            "type": "validates",
            "metadata": {
                "validation_point": "Phase 4",
                "required": True
            }
        },
        {
            "from": "style_guide",
            "to": "blog_sop",
            "type": "supports",
            "metadata": {
                "applicable_phases": ["Phase 2", "Phase 3"],
                "guidance_type": "writing_standards"
            }
        },
        {
            "from": "blog_template",
            "to": "blog_sop",
            "type": "implements",
            "metadata": {
                "phase": "Phase 2",
                "usage": "Structure for content creation"
            }
        },
        {
            "from": "performance_metrics",
            "to": "blog_sop",
            "type": "measures",
            "metadata": {
                "tracking_starts": "Post-publication",
                "review_cycle": "Weekly"
            }
        }
    ]
    
    for rel in relationships:
        if rel["from"] in entity_ids and rel["to"] in entity_ids:
            try:
                relation = RelationCreate(
                    fromId=str(entity_ids[rel["from"]]),
                    toId=str(entity_ids[rel["to"]]),
                    relationType=rel["type"],
                    metadata=rel["metadata"]
                )
                
                result = await manager.create_relations(
                    client_id=None,
                    actor_type=ACTOR_TYPE,
                    actor_id=ACTOR_ID,
                    relations=[relation]
                )
                
                logger.info(f"  ✅ Created relationship: {rel['from']} → {rel['type']} → {rel['to']}")
            except Exception as e:
                logger.error(f"  ❌ Error creating relationship {rel['from']} → {rel['to']}: {e}")
    
    # =============================
    # 8. SUMMARY
    # =============================
    logger.info("\n📊 Blog Writing Skill Storage Summary:")
    logger.info(f"  - Actor Type: {ACTOR_TYPE}")
    logger.info(f"  - Actor ID: {ACTOR_ID}")
    logger.info(f"  - Root Entity: Blog Writer Class (synth_class 24)")
    logger.info(f"  - Total Entities Created: {len(entity_ids)}")
    logger.info(f"  - Total Relationships: {len(relationships)}")
    logger.info("\nEntities created:")
    for name, id in entity_ids.items():
        logger.info(f"  - {name}: {id}")
    
    logger.info("\n⚡ Blog writing skill successfully stored!")
    logger.info("   All synths inheriting from class 24 can now access this knowledge")
    logger.info("   through hierarchical memory search.")
    
    # Close database connection
    db.close()

async def verify_skill_access(synth_id: UUID):
    """Verify that a synth can access the blog writing skill through hierarchy"""
    
    # Get database session
    db = next(get_db())
    
    # Initialize services
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    
    # Use HierarchicalMemoryManager for verification
    from services.memory_manager_hierarchical import HierarchicalMemoryManager
    manager = HierarchicalMemoryManager(db, embedding_service)
    
    logger.info(f"\n🔍 Verifying skill access for synth {synth_id}")
    logger.info("   (Synth should inherit from synth_class 24)")
    
    # Test queries
    test_queries = [
        "blog writing procedure",
        "quality checklist",
        "writing style guide",
        "blog template",
        "performance metrics"
    ]
    
    # We need the synth's client_id for hierarchical search
    # In a real system, this would come from the synth's record
    # For testing, we'll use a dummy client_id
    dummy_client_id = uuid4()
    
    for query in test_queries:
        logger.info(f"\n📌 Testing query: '{query}'")
        
        # Search with hierarchy (should find skill knowledge)
        try:
            hierarchical_results = await manager.search_hierarchical_memories(
                client_id=dummy_client_id,
                actor_type='synth',
                actor_id=synth_id,
                query=query,
                include_synth_class=True
            )
            
            logger.info(f"  Found {len(hierarchical_results)} results:")
            for result in hierarchical_results[:3]:
                logger.info(f"    - {result['entity_name']} (from {result.get('access_source', 'unknown')})")
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
    
    db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Store blog writing skill for synth_class 24"
    )
    parser.add_argument(
        "--verify-synth-id",
        type=str,
        help="Synth UUID to verify access (optional)"
    )
    
    args = parser.parse_args()
    
    # Store the skill
    asyncio.run(store_blog_writing_skill())
    
    # Optionally verify access
    if args.verify_synth_id:
        synth_id = UUID(args.verify_synth_id)
        asyncio.run(verify_skill_access(synth_id))