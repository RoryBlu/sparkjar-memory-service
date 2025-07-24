#!/usr/bin/env python3
"""
Store blog writing knowledge for synth_class 24 without client_id.

This script stores comprehensive blog writing procedures and knowledge
at the synth_class level, making them accessible to all synths of that class.
"""
import asyncio
import os
import sys
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from shared modules
from services.crew-api.src.database.models import MemoryEntities, MemoryObservations, MemoryRelations
from sparkjar_crew.shared.config.config import DATABASE_URL_DIRECT

# Create synchronous engine for this script
engine = create_engine(DATABASE_URL_DIRECT.replace('postgresql+asyncpg', 'postgresql'))
SessionLocal = sessionmaker(bind=engine)

def store_blog_writing_knowledge():
    """Store blog writing knowledge for synth_class 24"""
    
    print("🚀 Storing blog writing knowledge for synth_class 24")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Constants for synth_class level storage
        ACTOR_TYPE = 'synth_class'
        ACTOR_ID = str(uuid4())  # Generate a UUID for synth_class actor_id
        SYNTH_CLASS_ID = 24
        
        # Track entity IDs for relationships
        entity_ids = {}
        
        # =============================
        # 1. CREATE MAIN BLOG SOP ENTITY
        # =============================
        blog_sop = MemoryEntities(
            id=uuid4(),
            actor_type=ACTOR_TYPE,
            actor_id=UUID(ACTOR_ID),
            entity_name='Blog Writing Standard Operating Procedure v3.0',
            entity_type='procedure_template',
            metadata_json={
                "procedure_type": "blog_writing",
                "version": "3.0",
                "synth_class": SYNTH_CLASS_ID,
                "phases": [
                    "Research & Topic Analysis",
                    "Content Outlining",
                    "Writing & Optimization",
                    "Review & Publication"
                ],
                "total_duration": "2-4 hours",
                "prerequisites": ["Writing skills", "SEO knowledge", "Research abilities"],
                "deliverables": ["Blog post", "Meta data", "Images", "Social snippets"],
                "tags": ["writing", "blog", "seo", "content-creation", "sop"]
            },
            # description="Comprehensive guide for creating high-quality, SEO-optimized blog content",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(blog_sop)
        entity_ids['blog_sop'] = blog_sop.id
        print(f"  ✅ Created Blog SOP entity: {blog_sop.id}")
        
        # Add observations to Blog SOP
        sop_observations = [
            MemoryObservations(
                id=uuid4(),
                entity_id=blog_sop.id,
                observation_type='procedure_overview',
                value={
                    "purpose": "Standardized approach for creating high-quality, SEO-optimized blog content",
                    "scope": "Applies to all blog posts created by synth_class 24 agents",
                    "version_notes": "v3.0 adds AI-enhanced research and automated quality checks",
                    "expected_outputs": [
                        "SEO-optimized blog post (800-1500 words)",
                        "Meta title and description",
                        "Featured image selection",
                        "Internal/external link strategy",
                        "Social media snippets"
                    ],
                    "success_metrics": {
                        "readability_score": "60-70 (Flesch-Kincaid)",
                        "seo_score": "85+ (Yoast/similar)",
                        "engagement_target": "3+ minute read time",
                        "bounce_rate_target": "<40%",
                        "organic_traffic_growth": "10%+ MoM"
                    }
                },
                source='synth_class_24_template',
                observed_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            ),
            MemoryObservations(
                id=uuid4(),
                entity_id=blog_sop.id,
                observation_type='procedure_phase',
                value={
                    "phase": 1,
                    "name": "Research & Topic Analysis",
                    "duration": "30-60 minutes",
                    "objectives": [
                        "Understand search intent completely",
                        "Identify content gaps in current results",
                        "Gather authoritative sources and data"
                    ],
                    "steps": [
                        {
                            "step": "1.1",
                            "action": "Keyword Research & Intent Analysis",
                            "description": "Identify primary and secondary keywords with search intent",
                            "tools": ["Google Keyword Planner", "SEMrush", "Ahrefs"],
                            "deliverables": {
                                "primary_keyword": "1 main focus keyword",
                                "secondary_keywords": "3-5 related keywords",
                                "search_intent": "informational/transactional/navigational"
                            }
                        },
                        {
                            "step": "1.2",
                            "action": "Competitive Analysis",
                            "description": "Analyze top 10 ranking pages for the target keyword",
                            "tools": ["Google Search", "SEO tools"],
                            "deliverables": {
                                "content_gaps": "Topics competitors missed",
                                "average_word_count": "Benchmark for length",
                                "common_themes": "Must-cover topics"
                            }
                        },
                        {
                            "step": "1.3",
                            "action": "Source Gathering",
                            "description": "Collect authoritative sources and statistics",
                            "tools": ["Google Scholar", "Industry reports", "News sites"],
                            "deliverables": {
                                "sources": "5-10 authoritative references",
                                "statistics": "Relevant data points",
                                "quotes": "Expert opinions if applicable"
                            }
                        }
                    ]
                },
                source='synth_class_24_template',
                observed_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
        ]
        
        for obs in sop_observations:
            db.add(obs)
        
        # =============================
        # 2. CREATE BLOG CHECKLIST ENTITY
        # =============================
        blog_checklist = MemoryEntities(
            id=uuid4(),
            client_id=None,  # No client_id for synth_class!
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_type='checklist_template',
            name='Blog Quality Assurance Checklist',
            metadata={
                "checklist_type": "quality_assurance",
                "version": "2.1",
                "synth_class": SYNTH_CLASS_ID,
                "categories": [
                    {"name": "Content Quality", "weight": 0.35, "required_score": 0.8},
                    {"name": "SEO Optimization", "weight": 0.25, "required_score": 0.85},
                    {"name": "User Experience", "weight": 0.2, "required_score": 0.75},
                    {"name": "Technical Performance", "weight": 0.2, "required_score": 0.9}
                ],
                "passing_score": 0.85,
                "related_procedure": str(entity_ids['blog_sop'])
            },
            # description="Comprehensive quality checklist for blog posts before publication",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(blog_checklist)
        entity_ids['blog_checklist'] = blog_checklist.id
        print(f"  ✅ Created Blog Checklist entity: {blog_checklist.id}")
        
        # =============================
        # 3. CREATE WRITING STYLE GUIDE
        # =============================
        style_guide = MemoryEntities(
            id=uuid4(),
            client_id=None,  # No client_id for synth_class!
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_type='style_guide',
            name='Blog Writing Style Guide',
            metadata={
                "guide_type": "writing",
                "synth_class": SYNTH_CLASS_ID,
                "voice": "Professional yet conversational",
                "tone_variations": {
                    "technical_topics": "More formal, precise terminology",
                    "lifestyle_topics": "Casual, relatable, storytelling",
                    "business_topics": "Authoritative, data-driven"
                },
                "principles": [
                    {"name": "Clarity First", "description": "Simple language over complex jargon"},
                    {"name": "Active Voice", "description": "Use active voice 80%+ of the time"},
                    {"name": "Short Paragraphs", "description": "2-3 sentences max for web readability"},
                    {"name": "Visual Breaks", "description": "Use headers, bullets, images every 300 words"}
                ]
            },
            # description="Writing style standards for all blog content",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(style_guide)
        entity_ids['style_guide'] = style_guide.id
        print(f"  ✅ Created Style Guide entity: {style_guide.id}")
        
        # =============================
        # 4. CREATE SEO TECHNIQUES ENTITY
        # =============================
        seo_techniques = MemoryEntities(
            id=uuid4(),
            client_id=None,  # No client_id for synth_class!
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_type='knowledge_base',
            name='Advanced SEO Techniques for Blog Writing',
            metadata={
                "knowledge_type": "seo_optimization",
                "synth_class": SYNTH_CLASS_ID,
                "categories": ["on-page", "technical", "content"],
                "last_updated": datetime.utcnow().isoformat()
            },
            # description="Collection of proven SEO techniques for blog optimization",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(seo_techniques)
        entity_ids['seo_techniques'] = seo_techniques.id
        print(f"  ✅ Created SEO Techniques entity: {seo_techniques.id}")
        
        # Add SEO observations
        seo_observation = MemoryObservations(
            id=uuid4(),
            entity_id=seo_techniques.id,
            observation_type='writing_technique',
            value={
                "technique_type": "keyword_optimization",
                "category": "seo",
                "description": "Strategic keyword placement for maximum SEO impact",
                "examples": [
                    "Include primary keyword in H1, first paragraph, and conclusion",
                    "Use secondary keywords in H2/H3 headers naturally",
                    "Maintain 1-2% keyword density without stuffing"
                ],
                "when_to_use": "Every blog post targeting specific search terms",
                "effectiveness_rating": 4.8
            },
            source='synth_class_24_best_practices',
            observed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(seo_observation)
        
        # =============================
        # 5. CREATE RELATIONSHIPS
        # =============================
        relationships = [
            MemoryRelations(
                id=uuid4(),
                client_id=None,  # No client_id for synth_class!
                actor_type=ACTOR_TYPE,
                actor_id=ACTOR_ID,
                source_entity_id=entity_ids['blog_checklist'],
                target_entity_id=entity_ids['blog_sop'],
                relation_type='requires',
                metadata={
                    "requirement_type": "procedure",
                    "criticality": "mandatory",
                    "reason": "Checklist validates SOP was followed correctly"
                },
                # description="Quality checklist requires following the blog SOP",
                created_at=datetime.utcnow()
            ),
            MemoryRelations(
                id=uuid4(),
                client_id=None,  # No client_id for synth_class!
                actor_type=ACTOR_TYPE,
                actor_id=ACTOR_ID,
                source_entity_id=entity_ids['seo_techniques'],
                target_entity_id=entity_ids['blog_sop'],
                relation_type='enhances',
                metadata={
                    "enhancement_type": "optimization",
                    "value_added": "Improves search visibility and organic traffic",
                    "tested": True,
                    "adoption_rate": 0.95
                },
                # description="SEO techniques enhance the blog writing SOP",
                created_at=datetime.utcnow()
            ),
            MemoryRelations(
                id=uuid4(),
                client_id=None,  # No client_id for synth_class!
                actor_type=ACTOR_TYPE,
                actor_id=ACTOR_ID,
                source_entity_id=entity_ids['style_guide'],
                target_entity_id=entity_ids['blog_sop'],
                relation_type='enhances',
                metadata={
                    "enhancement_type": "consistency",
                    "value_added": "Ensures consistent voice and quality across all content",
                    "tested": True,
                    "adoption_rate": 1.0
                },
                # description="Style guide enhances blog writing consistency",
                created_at=datetime.utcnow()
            )
        ]
        
        for rel in relationships:
            db.add(rel)
        
        # Commit all changes
        db.commit()
        
        print("\n📊 Summary:")
        print(f"  - Created 4 memory entities")
        print(f"  - Added {len(sop_observations) + 1} observations")
        print(f"  - Created {len(relationships)} relationships")
        print(f"  - All stored for synth_class 24 (no client_id)")
        print("\n✅ Blog writing knowledge successfully stored!")
        
        return entity_ids
        
    except Exception as e:
        print(f"❌ Error storing blog knowledge: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    store_blog_writing_knowledge()