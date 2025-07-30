# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Store comprehensive blog writing knowledge for synth_class 24.
This uses the actual specifications from BLOG_WRITING_SOPS.md
and ensures data integrity with proper UUIDs.
"""
import os
import sys
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
# Add crew-api path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from crew-api models
from services.crew_api.src.database.models import MemoryEntities, MemoryObservations, MemoryRelations
from sparkjar_crew.shared.config.config import DATABASE_URL_DIRECT

# Create synchronous engine for this script
engine = create_engine(DATABASE_URL_DIRECT.replace('postgresql+asyncpg', 'postgresql'))
SessionLocal = sessionmaker(bind=engine)

def store_blog_writing_knowledge():
    """Store comprehensive blog writing knowledge for synth_class 24"""
    
    logger.info("🚀 Storing comprehensive blog writing knowledge for synth_class 24")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Constants for synth_class 24
        ACTOR_TYPE = 'synth_class'
        # Use the actor_id that's already in the database for synth_class 24
        ACTOR_ID = UUID('00000000-0000-0000-0000-000000000024')
        SYNTH_CLASS_ID = 24
        
        # First, verify synth_class 24 exists
        from services.crew_api.src.database.models import SynthClasses
        synth_class = db.query(SynthClasses).filter(
            SynthClasses.id == SYNTH_CLASS_ID
        ).first()
        
        if not synth_class:
            logger.info(f"❌ Synth class {SYNTH_CLASS_ID} not found!")
            return
        
        logger.info(f"✅ Found synth_class {SYNTH_CLASS_ID}: {synth_class.title}")
        logger.info(f"   Using actor_id: {ACTOR_ID}")
        
        # Track entity IDs for relationships
        entity_ids = {}
        
        # =============================
        # 1. BLOG WRITING SOP - MAIN PROCEDURE
        # =============================
        blog_sop = MemoryEntities(
            id=uuid4(),
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_name='Blog Writing Standard Operating Procedure v4.0',
            entity_type='procedure_template',
            metadata_json={
                "procedure_type": "blog_writing",
                "version": "4.0",
                "synth_class": SYNTH_CLASS_ID,
                "phases": [
                    "Research & Planning (45-60 min)",
                    "Content Creation (90-120 min)",
                    "Optimization & Enhancement (30-45 min)",
                    "Quality Assurance (20-30 min)"
                ],
                "total_duration": "3-4 hours",
                "output_specs": {
                    "word_count": "1500-2500",
                    "readability_score": "60-70",
                    "seo_score": "85+",
                    "quality_threshold": "85%"
                },
                "prerequisites": [
                    "Writing proficiency",
                    "SEO knowledge",
                    "Research skills",
                    "Tool familiarity"
                ],
                "deliverables": [
                    "SEO-optimized blog post",
                    "Meta descriptions",
                    "Social media snippets",
                    "Visual assets",
                    "Performance metrics"
                ]
            },
            deleted_at=None
        )
        db.add(blog_sop)
        entity_ids['blog_sop'] = blog_sop.id
        logger.info(f"  ✅ Created Blog SOP entity: {blog_sop.id}")
        
        # Add detailed phase observations
        phase_observations = [
            # Phase 1: Research & Planning
            MemoryObservations(
                id=uuid4(),
                entity_id=blog_sop.id,
                observation_type='procedure_phase',
                observation_value={
                    "phase": 1,
                    "name": "Research & Planning",
                    "duration": "45-60 minutes",
                    "objectives": [
                        "Understand topic and search intent",
                        "Analyze competition and content gaps",
                        "Define unique angle and value proposition",
                        "Create comprehensive content outline"
                    ],
                    "steps": [
                        {
                            "step": "1.1",
                            "name": "Topic Analysis",
                            "tasks": [
                                "Conduct keyword research",
                                "Analyze search intent",
                                "Review top 10 SERP results",
                                "Identify content gaps",
                                "Define unique angle"
                            ],
                            "outputs": [
                                "Primary keyword with metrics",
                                "Related keywords and LSI terms",
                                "Competitor analysis",
                                "Unique value proposition"
                            ]
                        },
                        {
                            "step": "1.2",
                            "name": "Audience Research",
                            "tasks": [
                                "Define reader persona",
                                "Identify pain points",
                                "Determine knowledge level",
                                "Map reader journey",
                                "List objections"
                            ],
                            "outputs": [
                                "Persona profile",
                                "Challenge map",
                                "Content preferences"
                            ]
                        },
                        {
                            "step": "1.3",
                            "name": "Content Planning",
                            "tasks": [
                                "Create H2/H3 outline",
                                "Allocate word counts",
                                "Plan supporting elements",
                                "Set measurable goals",
                                "Define success metrics"
                            ],
                            "outputs": [
                                "Content blueprint",
                                "Section breakdown",
                                "Media requirements"
                            ]
                        }
                    ]
                },
                source='synth_class_24_sop_v4'
            ),
            # Phase 2: Content Creation
            MemoryObservations(
                id=uuid4(),
                entity_id=blog_sop.id,
                observation_type='procedure_phase',
                observation_value={
                    "phase": 2,
                    "name": "Content Creation",
                    "duration": "90-120 minutes",
                    "objectives": [
                        "Write compelling introduction with hook",
                        "Develop comprehensive body content",
                        "Craft action-oriented conclusion",
                        "Maintain consistent voice and tone"
                    ],
                    "components": {
                        "introduction": {
                            "hook_types": [
                                "Question hook",
                                "Statistic hook", 
                                "Story hook",
                                "Problem hook",
                                "Quote hook"
                            ],
                            "structure": [
                                "Hook (1-2 sentences)",
                                "Context (2-3 sentences)",
                                "Thesis statement",
                                "Value preview",
                                "Transition"
                            ]
                        },
                        "body": {
                            "paragraph_structure": [
                                "Topic sentence",
                                "Evidence",
                                "Analysis",
                                "Transition"
                            ],
                            "engagement_techniques": [
                                "Direct address (you)",
                                "Specific examples",
                                "Visual breaks",
                                "Bullet points",
                                "Actionable tips"
                            ]
                        },
                        "conclusion": {
                            "elements": [
                                "Main points recap",
                                "Value reinforcement",
                                "Broader implications",
                                "Clear CTA",
                                "Next steps"
                            ]
                        }
                    }
                },
                source='synth_class_24_sop_v4'
            ),
            # Phase 3: Optimization
            MemoryObservations(
                id=uuid4(),
                entity_id=blog_sop.id,
                observation_type='procedure_phase',
                observation_value={
                    "phase": 3,
                    "name": "Optimization & Enhancement",
                    "duration": "30-45 minutes",
                    "objectives": [
                        "Optimize for search engines",
                        "Enhance readability",
                        "Add visual elements",
                        "Improve user experience"
                    ],
                    "tasks": {
                        "seo_optimization": {
                            "elements": [
                                "Title tag optimization",
                                "Meta description",
                                "Header hierarchy",
                                "Keyword placement (1-2%)",
                                "Alt text for images",
                                "Internal links (3-5)",
                                "External links (2-3)"
                            ]
                        },
                        "readability": {
                            "checks": [
                                "Sentence variation",
                                "Paragraph length (2-4 sentences)",
                                "Transition words",
                                "Active voice (>80%)",
                                "Flesch score (60-70)"
                            ]
                        },
                        "visual_enhancement": {
                            "requirements": [
                                "Featured image (1200x630px)",
                                "Section images (every 300-400 words)",
                                "Infographics for data",
                                "Annotated screenshots"
                            ]
                        }
                    }
                },
                source='synth_class_24_sop_v4'
            ),
            # Phase 4: Quality Assurance
            MemoryObservations(
                id=uuid4(),
                entity_id=blog_sop.id,
                observation_type='procedure_phase',
                observation_value={
                    "phase": 4,
                    "name": "Quality Assurance",
                    "duration": "20-30 minutes",
                    "objectives": [
                        "Verify content accuracy",
                        "Ensure technical quality",
                        "Validate performance metrics",
                        "Confirm publication readiness"
                    ],
                    "checklists": {
                        "content_review": [
                            "Factual accuracy verified",
                            "Sources properly cited",
                            "Grammar and spelling checked",
                            "Tone consistency maintained",
                            "Brand voice aligned",
                            "Value clearly delivered",
                            "CTA compelling"
                        ],
                        "technical_review": [
                            "All links functional",
                            "Images optimized (<100KB)",
                            "Mobile responsive",
                            "Load time <3 seconds",
                            "Schema markup implemented",
                            "Social cards configured"
                        ],
                        "quality_scoring": {
                            "content_quality": "40%",
                            "seo_optimization": "30%",
                            "user_experience": "20%",
                            "technical_performance": "10%",
                            "minimum_score": "85%"
                        }
                    }
                },
                source='synth_class_24_sop_v4'
            )
        ]
        
        for obs in phase_observations:
            db.add(obs)
        
        # =============================
        # 2. BLOG STRUCTURE TEMPLATE
        # =============================
        blog_structure = MemoryEntities(
            id=uuid4(),
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_name='Blog Post JSON Structure Template',
            entity_type='data_template',
            metadata_json={
                "template_type": "blog_post_structure",
                "version": "2.0",
                "synth_class": SYNTH_CLASS_ID,
                "schema": {
                    "metadata": {
                        "title": "50-60 chars",
                        "slug": "url-friendly",
                        "author": {
                            "name": "string",
                            "synth_id": "uuid",
                            "synth_class": 24
                        },
                        "dates": {
                            "publication": "ISO 8601",
                            "last_modified": "ISO 8601"
                        },
                        "status": ["draft", "review", "published", "archived"]
                    },
                    "seo": {
                        "meta_description": "150-160 chars",
                        "keywords": {
                            "primary": "string",
                            "secondary": ["array"]
                        },
                        "schema_markup": "BlogPosting"
                    },
                    "structure": {
                        "introduction": {
                            "hook": "string",
                            "context": "string",
                            "thesis": "string",
                            "preview": ["array"]
                        },
                        "sections": [
                            {
                                "heading": "H2/H3",
                                "content": "paragraphs",
                                "media": "optional"
                            }
                        ],
                        "conclusion": {
                            "summary": "bullets",
                            "cta": "string"
                        }
                    }
                }
            },
            deleted_at=None
        )
        db.add(blog_structure)
        entity_ids['blog_structure'] = blog_structure.id
        logger.info(f"  ✅ Created Blog Structure Template: {blog_structure.id}")
        
        # =============================
        # 3. CONTENT TYPE VARIATIONS
        # =============================
        content_variations = MemoryEntities(
            id=uuid4(),
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_name='Blog Content Type Variations Guide',
            entity_type='knowledge_base',
            metadata_json={
                "knowledge_type": "content_variations",
                "synth_class": SYNTH_CLASS_ID,
                "content_types": [
                    "How-To Posts",
                    "Listicles",
                    "Ultimate Guides",
                    "Case Studies"
                ]
            },
            deleted_at=None
        )
        db.add(content_variations)
        entity_ids['content_variations'] = content_variations.id
        logger.info(f"  ✅ Created Content Variations Guide: {content_variations.id}")
        
        # Add observations for each content type
        content_type_observations = [
            MemoryObservations(
                id=uuid4(),
                entity_id=content_variations.id,
                observation_type='content_type_spec',
                observation_value={
                    "type": "How-To Posts",
                    "characteristics": [
                        "Step-by-step structure",
                        "Numbered lists",
                        "Process screenshots",
                        "Difficulty indicators",
                        "Time estimates"
                    ],
                    "best_for": "Teaching specific skills or processes",
                    "typical_length": "1000-2000 words",
                    "engagement_pattern": "High task completion rate"
                },
                source='synth_class_24_content_guide'
            ),
            MemoryObservations(
                id=uuid4(),
                entity_id=content_variations.id,
                observation_type='content_type_spec',
                observation_value={
                    "type": "Listicles",
                    "characteristics": [
                        "Compelling number in title",
                        "Consistent formatting",
                        "Progressive value increase",
                        "Visual separators",
                        "Quick summaries"
                    ],
                    "best_for": "Scannable, shareable content",
                    "typical_length": "1200-1800 words",
                    "engagement_pattern": "High social shares"
                },
                source='synth_class_24_content_guide'
            ),
            MemoryObservations(
                id=uuid4(),
                entity_id=content_variations.id,
                observation_type='content_type_spec',
                observation_value={
                    "type": "Ultimate Guides",
                    "characteristics": [
                        "Comprehensive coverage",
                        "Table of contents",
                        "Chapter structure",
                        "Downloadable resources",
                        "Expert quotes"
                    ],
                    "best_for": "Establishing authority on topic",
                    "typical_length": "3000-5000 words",
                    "engagement_pattern": "High time on page"
                },
                source='synth_class_24_content_guide'
            ),
            MemoryObservations(
                id=uuid4(),
                entity_id=content_variations.id,
                observation_type='content_type_spec',
                observation_value={
                    "type": "Case Studies",
                    "characteristics": [
                        "Problem-solution format",
                        "Data visualization",
                        "Results emphasis",
                        "Methodology section",
                        "Lessons learned"
                    ],
                    "best_for": "Demonstrating real-world results",
                    "typical_length": "1500-2500 words",
                    "engagement_pattern": "High conversion rate"
                },
                source='synth_class_24_content_guide'
            )
        ]
        
        for obs in content_type_observations:
            db.add(obs)
        
        # =============================
        # 4. WRITING STYLE GUIDE
        # =============================
        style_guide = MemoryEntities(
            id=uuid4(),
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_name='Blog Writing Style & Voice Guide',
            entity_type='style_guide',
            metadata_json={
                "guide_type": "writing_style",
                "synth_class": SYNTH_CLASS_ID,
                "voice": "Professional yet conversational",
                "tone_variations": {
                    "educational": "Clear, patient, thorough",
                    "inspirational": "Uplifting, motivating, empowering",
                    "analytical": "Data-driven, logical, objective",
                    "persuasive": "Compelling, benefit-focused, action-oriented"
                },
                "writing_principles": [
                    {
                        "principle": "Clarity First",
                        "implementation": "Simple words over jargon, short sentences for complex ideas"
                    },
                    {
                        "principle": "Reader-Centric",
                        "implementation": "Focus on 'you' and reader benefits, address pain points directly"
                    },
                    {
                        "principle": "Evidence-Based",
                        "implementation": "Support claims with data, cite credible sources, use specific examples"
                    },
                    {
                        "principle": "Action-Oriented",
                        "implementation": "Include actionable takeaways, provide clear next steps"
                    }
                ],
                "grammar_preferences": {
                    "oxford_comma": True,
                    "contractions": "allowed for conversational tone",
                    "sentence_length": "vary between 10-20 words",
                    "paragraph_length": "2-4 sentences max"
                }
            },
            deleted_at=None
        )
        db.add(style_guide)
        entity_ids['style_guide'] = style_guide.id
        logger.info(f"  ✅ Created Style Guide: {style_guide.id}")
        
        # =============================
        # 5. QUALITY CHECKLIST
        # =============================
        quality_checklist = MemoryEntities(
            id=uuid4(),
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_name='Blog Post Quality Assurance Checklist',
            entity_type='checklist_template',
            metadata_json={
                "checklist_type": "blog_quality_assurance",
                "version": "3.0",
                "synth_class": SYNTH_CLASS_ID,
                "categories": [
                    {
                        "name": "Content Quality",
                        "weight": 0.4,
                        "items": [
                            "Value clearly delivered",
                            "Claims supported by evidence",
                            "Unique insights provided",
                            "Comprehensive coverage",
                            "Actionable takeaways included"
                        ]
                    },
                    {
                        "name": "SEO Optimization",
                        "weight": 0.3,
                        "items": [
                            "Title optimized (50-60 chars)",
                            "Meta description compelling",
                            "Keywords naturally integrated",
                            "Headers properly structured",
                            "Internal/external links added"
                        ]
                    },
                    {
                        "name": "User Experience",
                        "weight": 0.2,
                        "items": [
                            "Easy to scan and read",
                            "Visuals enhance understanding",
                            "Mobile-friendly formatting",
                            "Clear navigation structure",
                            "Fast page load time"
                        ]
                    },
                    {
                        "name": "Technical Quality",
                        "weight": 0.1,
                        "items": [
                            "Grammar and spelling perfect",
                            "Links all functional",
                            "Images optimized",
                            "Schema markup present",
                            "Social cards configured"
                        ]
                    }
                ],
                "passing_score": 0.85,
                "related_procedure": str(entity_ids['blog_sop'])
            },
            deleted_at=None
        )
        db.add(quality_checklist)
        entity_ids['quality_checklist'] = quality_checklist.id
        logger.info(f"  ✅ Created Quality Checklist: {quality_checklist.id}")
        
        # =============================
        # 6. SEO BEST PRACTICES
        # =============================
        seo_practices = MemoryEntities(
            id=uuid4(),
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_name='Blog SEO Best Practices Knowledge Base',
            entity_type='knowledge_base',
            metadata_json={
                "knowledge_type": "seo_optimization",
                "synth_class": SYNTH_CLASS_ID,
                "categories": [
                    "on-page",
                    "technical",
                    "content",
                    "user-signals"
                ],
                "last_updated": datetime.utcnow().isoformat()
            },
            deleted_at=None
        )
        db.add(seo_practices)
        entity_ids['seo_practices'] = seo_practices.id
        logger.info(f"  ✅ Created SEO Practices: {seo_practices.id}")
        
        # Add SEO observations
        seo_observation = MemoryObservations(
            id=uuid4(),
            entity_id=seo_practices.id,
            observation_type='seo_technique',
            observation_value={
                "technique": "E-A-T Optimization",
                "category": "content",
                "description": "Establish Expertise, Authoritativeness, and Trustworthiness",
                "implementation": [
                    "Include author bio with credentials",
                    "Cite authoritative sources",
                    "Show real expertise through depth",
                    "Update content regularly",
                    "Include case studies and data"
                ],
                "impact": "Critical for YMYL topics",
                "priority": "high"
            },
            source='synth_class_24_seo_guide'
        )
        db.add(seo_observation)
        
        # =============================
        # 7. CREATE RELATIONSHIPS
        # =============================
        relationships = [
            # SOP requires the structure template
            MemoryRelations(
                id=uuid4(),
                from_entity_id=entity_ids['blog_sop'],
                to_entity_id=entity_ids['blog_structure'],
                relation_type='requires',
                metadata_json={
                    "requirement_type": "template",
                    "criticality": "mandatory",
                    "reason": "SOP outputs must follow the JSON structure"
                },
                deleted_at=None
            ),
            # Quality checklist validates SOP execution
            MemoryRelations(
                id=uuid4(),
                from_entity_id=entity_ids['quality_checklist'],
                to_entity_id=entity_ids['blog_sop'],
                relation_type='validates',
                metadata_json={
                    "validation_type": "quality_assurance",
                    "threshold": 0.85,
                    "frequency": "every_post"
                },
                deleted_at=None
            ),
            # Style guide enhances SOP
            MemoryRelations(
                id=uuid4(),
                from_entity_id=entity_ids['style_guide'],
                to_entity_id=entity_ids['blog_sop'],
                relation_type='enhances',
                metadata_json={
                    "enhancement_type": "consistency",
                    "value": "Ensures uniform voice across all content"
                },
                deleted_at=None
            ),
            # SEO practices enhance SOP
            MemoryRelations(
                id=uuid4(),
                from_entity_id=entity_ids['seo_practices'],
                to_entity_id=entity_ids['blog_sop'],
                relation_type='enhances',
                metadata_json={
                    "enhancement_type": "performance",
                    "value": "Improves search visibility and organic traffic"
                },
                deleted_at=None
            ),
            # Content variations extend SOP
            MemoryRelations(
                id=uuid4(),
                from_entity_id=entity_ids['content_variations'],
                to_entity_id=entity_ids['blog_sop'],
                relation_type='extends',
                metadata_json={
                    "extension_type": "specialization",
                    "value": "Provides specific adaptations for content types"
                },
                deleted_at=None
            )
        ]
        
        for rel in relationships:
            db.add(rel)
        
        # Commit all changes
        db.commit()
        
        logger.info("\n📊 Summary:")
        logger.info(f"  - Created 6 memory entities")
        logger.info(f"  - Added {len(phase_observations) + len(content_type_observations) + 1} observations")
        logger.info(f"  - Created {len(relationships)} relationships")
        logger.info(f"  - All stored for synth_class {SYNTH_CLASS_ID} ({synth_class.title})")
        logger.info(f"  - Actor ID: {ACTOR_ID}")
        logger.info("\n✅ Blog writing knowledge successfully stored with full integrity!")
        
        return entity_ids
        
    except Exception as e:
        logger.error(f"❌ Error storing blog knowledge: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    store_blog_writing_knowledge()