# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Store blog writing procedures for synth_class 24 using hierarchical memory system.

This script demonstrates the proper way to store procedures at the synth_class level
so that all synths based on that class can access them through hierarchical search.
"""
import asyncio
import os
import sys
from uuid import UUID, uuid4
from datetime import datetime

# Add parent directory to path

from database import get_db
from services.memory_manager_hierarchical import HierarchicalMemoryManager
from services.embeddings import EmbeddingService
from sparkjar_crew.shared.schemas.memory_schemas import EntityCreate, ObservationCreate, RelationCreate
from config import settings

async def store_blog_procedures(client_id: UUID, synth_class_id: int = 24):
    """Store comprehensive blog writing procedures at synth_class level"""
    
    # Get database session
    db = next(get_db())
    
    # Initialize services
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    
    manager = HierarchicalMemoryManager(db, embedding_service)
    
    logger.info(f"🚀 Storing blog procedures for synth_class {synth_class_id}")
    
    # Create the main blog writing SOP
    blog_sop = EntityCreate(
        name="Blog Writing Standard Operating Procedure v3.0",
        entityType="procedure_template",
        metadata={
            "procedure_type": "blog_writing",
            "version": "3.0",
            "synth_class": synth_class_id,
            "created_date": datetime.utcnow().isoformat(),
            "tags": ["writing", "blog", "seo", "content-creation", "sop"],
            "estimated_time": "2-4 hours",
            "skill_level": "intermediate",
            "last_updated": datetime.utcnow().isoformat()
        },
        observations=[
            ObservationCreate(
                type="procedure_overview",
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
                source="synth_class_24_template"
            ),
            ObservationCreate(
                type="procedure_phase",
                value={
                    "phase": 1,
                    "name": "Research & Topic Analysis",
                    "duration": "30-60 minutes",
                    "critical": True,
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
                            "tools": ["Google Keyword Planner", "SEMrush", "Ahrefs", "AnswerThePublic"],
                            "deliverables": {
                                "primary_keyword": {
                                    "count": 1,
                                    "criteria": "Search volume >500/month, difficulty <50"
                                },
                                "secondary_keywords": {
                                    "count": "3-5",
                                    "criteria": "Related terms, long-tail variations"
                                },
                                "search_intent": {
                                    "types": ["informational", "commercial", "transactional", "navigational"],
                                    "match_content": True
                                }
                            },
                            "quality_checks": [
                                "Verify keyword relevance to topic",
                                "Confirm search volume data is recent",
                                "Check keyword difficulty is achievable"
                            ]
                        },
                        {
                            "step": "1.2",
                            "action": "Competitive SERP Analysis",
                            "description": "Analyze top 10 search results for insights",
                            "checklist": [
                                "Average word count of top results",
                                "Common topics and subtopics covered",
                                "Content formats (how-to, listicle, guide, etc.)",
                                "Featured snippets opportunities",
                                "People Also Ask questions",
                                "Related searches at bottom of SERP",
                                "Domain authority of competitors",
                                "Content freshness (publication dates)"
                            ],
                            "deliverables": {
                                "content_gap_analysis": "Topics competitors missed",
                                "unique_angle": "Our differentiation approach",
                                "target_word_count": "Based on SERP average +10%"
                            }
                        },
                        {
                            "step": "1.3",
                            "action": "Source & Data Research",
                            "description": "Gather credible sources and supporting data",
                            "requirements": {
                                "primary_sources": {
                                    "minimum": 3,
                                    "criteria": "Authoritative, recent, relevant"
                                },
                                "statistics": {
                                    "minimum": 2,
                                    "criteria": "Verifiable, impactful, recent"
                                },
                                "expert_quotes": {
                                    "minimum": 1,
                                    "criteria": "Industry recognized experts"
                                },
                                "case_studies": {
                                    "minimum": 1,
                                    "criteria": "Relevant, detailed, successful"
                                }
                            },
                            "source_evaluation": [
                                "Check publication date (<2 years old preferred)",
                                "Verify author credentials",
                                "Confirm data accuracy",
                                "Assess source bias"
                            ]
                        }
                    ],
                    "phase_output": {
                        "research_document": "Complete research findings",
                        "keyword_map": "Primary and secondary keywords with intent",
                        "content_outline": "Initial structure based on research"
                    }
                },
                source="synth_class_24_template"
            ),
            ObservationCreate(
                type="procedure_phase",
                value={
                    "phase": 2,
                    "name": "Content Planning & Structure",
                    "duration": "20-30 minutes",
                    "prerequisites": ["Phase 1 completed"],
                    "objectives": [
                        "Create compelling, SEO-friendly headline",
                        "Develop logical content flow",
                        "Plan multimedia elements"
                    ],
                    "steps": [
                        {
                            "step": "2.1",
                            "action": "Headline Creation & Optimization",
                            "description": "Craft attention-grabbing, SEO-optimized title",
                            "headline_formulas": [
                                "{Number} + {Adjective} + {Keyword} + {Promise}",
                                "How to {Achieve Desired Outcome} in {Time Frame}",
                                "The Ultimate Guide to {Keyword} ({Current Year})",
                                "{Keyword}: {Number} {Things} You Need to Know",
                                "Why {Statement} (And How to {Solution})",
                                "{Number} {Keyword} Mistakes (And How to Avoid Them)"
                            ],
                            "requirements": [
                                "Length: 50-60 characters for SEO",
                                "Include primary keyword naturally",
                                "Create curiosity or urgency",
                                "Make specific, measurable promise",
                                "Use power words (Ultimate, Essential, Proven)",
                                "Front-load important words"
                            ],
                            "testing": {
                                "create_variations": 3,
                                "test_criteria": ["Click appeal", "SEO score", "Clarity"],
                                "tools": ["CoSchedule Headline Analyzer", "Sharethrough"]
                            }
                        },
                        {
                            "step": "2.2",
                            "action": "Content Structure Development",
                            "description": "Create detailed blog post outline",
                            "outline_components": {
                                "introduction": {
                                    "elements": [
                                        "Hook (question, statistic, story)",
                                        "Problem identification",
                                        "Solution preview",
                                        "Article roadmap"
                                    ],
                                    "word_count": "100-150 words",
                                    "requirements": [
                                        "Include primary keyword in first 100 words",
                                        "State clear value proposition",
                                        "Set expectations for reader"
                                    ]
                                },
                                "body_sections": {
                                    "count": "3-5 main sections",
                                    "structure": {
                                        "h2_headers": "Main topic areas",
                                        "h3_headers": "Subtopics within sections",
                                        "h4_headers": "Detailed points if needed"
                                    },
                                    "section_length": "200-300 words each",
                                    "flow": [
                                        "Problem → Solution",
                                        "Simple → Complex",
                                        "Theory → Practice"
                                    ]
                                },
                                "conclusion": {
                                    "elements": [
                                        "Key points summary",
                                        "Main takeaway emphasis",
                                        "Clear call-to-action",
                                        "Next steps for reader"
                                    ],
                                    "word_count": "100-150 words",
                                    "cta_types": [
                                        "Subscribe to newsletter",
                                        "Download related resource",
                                        "Try product/service",
                                        "Read related article"
                                    ]
                                }
                            }
                        },
                        {
                            "step": "2.3",
                            "action": "Multimedia Planning",
                            "description": "Plan visual and interactive elements",
                            "requirements": {
                                "featured_image": {
                                    "dimensions": "1200x630px minimum",
                                    "format": "JPG or WebP",
                                    "style": "Professional, relevant, eye-catching",
                                    "text_overlay": "Optional title overlay",
                                    "alt_text": "Descriptive, keyword-inclusive"
                                },
                                "body_images": {
                                    "frequency": "1 per 300-400 words",
                                    "types": [
                                        "Screenshots with annotations",
                                        "Infographics",
                                        "Charts and graphs",
                                        "Process diagrams",
                                        "Stock photos (sparingly)"
                                    ],
                                    "requirements": [
                                        "Compressed for web (<100KB)",
                                        "Consistent style",
                                        "Mobile-responsive",
                                        "Meaningful captions"
                                    ]
                                },
                                "other_media": {
                                    "videos": "Embed relevant tutorials",
                                    "gifs": "For process demonstration",
                                    "interactive": "Calculators, quizzes if relevant",
                                    "downloads": "Templates, checklists"
                                }
                            }
                        }
                    ],
                    "phase_output": {
                        "final_headline": "SEO-optimized title",
                        "content_outline": "Detailed structure with word counts",
                        "media_plan": "List of required visual assets"
                    }
                },
                source="synth_class_24_template"
            ),
            ObservationCreate(
                type="procedure_phase",
                value={
                    "phase": 3,
                    "name": "Content Writing & Optimization",
                    "duration": "60-90 minutes",
                    "prerequisites": ["Phase 2 completed", "Research document available"],
                    "objectives": [
                        "Write engaging, valuable content",
                        "Maintain consistent voice and tone",
                        "Optimize for both readers and search engines"
                    ],
                    "writing_guidelines": {
                        "voice_and_tone": {
                            "voice": "Professional yet conversational",
                            "tone": "Helpful, authoritative, approachable",
                            "perspective": "Second person ('you') for engagement",
                            "brand_alignment": "Match company voice guide"
                        },
                        "readability": {
                            "sentence_length": {
                                "average": "15-20 words",
                                "maximum": "30 words",
                                "variety": "Mix short and medium sentences"
                            },
                            "paragraph_length": {
                                "sentences": "2-3 maximum",
                                "lines": "3-4 on desktop",
                                "mobile_friendly": True
                            },
                            "vocabulary": {
                                "level": "8th-9th grade",
                                "jargon": "Explain when necessary",
                                "active_voice": "80%+ of sentences"
                            }
                        },
                        "engagement_techniques": [
                            "Start with compelling hook",
                            "Use storytelling elements",
                            "Include specific examples",
                            "Ask rhetorical questions",
                            "Use analogies and metaphors",
                            "Add personal insights",
                            "Create 'aha' moments"
                        ]
                    },
                    "seo_integration": {
                        "keyword_placement": [
                            "Primary keyword in first 100 words",
                            "Include in 1-2 H2 headers",
                            "Natural density 1-2%",
                            "Use variations and synonyms",
                            "Include in meta description",
                            "Add to image alt text"
                        ],
                        "semantic_seo": [
                            "Use LSI keywords throughout",
                            "Answer related questions",
                            "Cover topic comprehensively",
                            "Include entities and concepts"
                        ],
                        "technical_elements": [
                            "Optimize URL slug",
                            "Internal linking (2-3 relevant)",
                            "External linking (1-2 authorities)",
                            "Anchor text variation"
                        ]
                    },
                    "writing_process": {
                        "first_draft": {
                            "focus": "Get ideas down",
                            "speed": "Write without editing",
                            "goal": "Complete coverage"
                        },
                        "revision": {
                            "structure": "Check logical flow",
                            "clarity": "Simplify complex sentences",
                            "engagement": "Add hooks and stories"
                        },
                        "optimization": {
                            "seo": "Add keywords naturally",
                            "readability": "Improve sentence variety",
                            "value": "Ensure actionable advice"
                        }
                    }
                },
                source="synth_class_24_template"
            ),
            ObservationCreate(
                type="procedure_phase",
                value={
                    "phase": 4,
                    "name": "Quality Assurance & Publishing",
                    "duration": "30-40 minutes",
                    "critical": True,
                    "objectives": [
                        "Ensure content quality and accuracy",
                        "Optimize all technical elements",
                        "Prepare for successful publication"
                    ],
                    "quality_checklist": {
                        "content_quality": {
                            "accuracy": [
                                "Fact-check all statistics",
                                "Verify source citations",
                                "Confirm data currency",
                                "Check calculation accuracy"
                            ],
                            "value": [
                                "Provides unique insights",
                                "Answers search intent fully",
                                "Includes actionable advice",
                                "Better than competition"
                            ],
                            "writing": [
                                "Grammar and spelling perfect",
                                "Consistent style throughout",
                                "Smooth transitions",
                                "Engaging from start to finish"
                            ]
                        },
                        "technical_optimization": {
                            "on_page_seo": [
                                "Title tag (50-60 chars)",
                                "Meta description (150-160 chars)",
                                "URL slug optimized",
                                "Header hierarchy correct",
                                "Image alt text complete",
                                "Schema markup added"
                            ],
                            "performance": [
                                "Images compressed",
                                "Page load <3 seconds",
                                "Mobile-responsive",
                                "Core Web Vitals passing"
                            ],
                            "links": [
                                "All links working",
                                "Internal links relevant",
                                "External links authoritative",
                                "No broken redirects"
                            ]
                        },
                        "pre_publish": {
                            "final_review": [
                                "Read entire post aloud",
                                "Check formatting consistency",
                                "Verify all media loads",
                                "Test on mobile device"
                            ],
                            "meta_elements": [
                                "Social media images set",
                                "OG tags configured",
                                "Categories selected",
                                "Tags added (3-5)",
                                "Author bio updated"
                            ],
                            "promotion_ready": [
                                "Social media posts drafted",
                                "Email newsletter snippet",
                                "Key quotes identified",
                                "Distribution plan set"
                            ]
                        }
                    },
                    "tools": {
                        "grammar": ["Grammarly", "Hemingway Editor"],
                        "seo": ["Yoast SEO", "RankMath", "Surfer SEO"],
                        "plagiarism": ["Copyscape", "Grammarly Premium"],
                        "performance": ["PageSpeed Insights", "GTmetrix"]
                    },
                    "sign_off": {
                        "checklist_complete": "All items checked",
                        "quality_score": "85+ on all metrics",
                        "ready_to_publish": True
                    }
                },
                source="synth_class_24_template"
            ),
            ObservationCreate(
                type="supplementary_guidelines",
                value={
                    "common_mistakes": [
                        "Keyword stuffing - Keep it natural",
                        "Thin content - Provide real value",
                        "No CTA - Always guide next action",
                        "Poor formatting - Make it scannable",
                        "Ignoring mobile - Test on devices",
                        "No images - Break up text visually",
                        "Weak headline - Spend time perfecting",
                        "No internal links - Connect content",
                        "Grammar errors - Always proofread",
                        "Outdated info - Verify currency"
                    ],
                    "advanced_techniques": [
                        "Topic clusters for authority",
                        "Featured snippet optimization",
                        "Voice search optimization",
                        "E-A-T signals enhancement",
                        "User intent matching",
                        "Semantic keyword research",
                        "Content pruning strategy",
                        "Conversion optimization"
                    ],
                    "performance_tracking": [
                        "Organic traffic growth",
                        "Keyword ranking improvements",
                        "Engagement metrics (time, bounce)",
                        "Social shares and backlinks",
                        "Conversion rate from blog",
                        "Return visitor rate"
                    ]
                },
                source="synth_class_24_template"
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
        
        blog_sop_id = UUID(result[0]['id'])
        logger.info(f"✅ Created Blog SOP with ID: {blog_sop_id}")
        
    except Exception as e:
        logger.error(f"❌ Error creating Blog SOP: {e}")
        db.close()
        return
    
    # Create Quality Checklist as a separate entity
    quality_checklist = EntityCreate(
        name="Blog Post Quality Assurance Checklist",
        entityType="checklist_template",
        metadata={
            "checklist_type": "quality_assurance",
            "version": "3.0",
            "synth_class": synth_class_id,
            "related_procedure": str(blog_sop_id)
        },
        observations=[
            ObservationCreate(
                type="checklist_category",
                value={
                    "category": "Content Quality",
                    "weight": 0.4,
                    "required_score": 0.9,
                    "checks": [
                        {
                            "item": "Provides unique value not found elsewhere",
                            "required": True,
                            "weight": 0.3
                        },
                        {
                            "item": "Fully answers the search intent",
                            "required": True,
                            "weight": 0.3
                        },
                        {
                            "item": "Includes specific, actionable advice",
                            "required": True,
                            "weight": 0.2
                        },
                        {
                            "item": "Uses recent data and examples",
                            "required": False,
                            "weight": 0.1
                        },
                        {
                            "item": "Free of fluff and filler content",
                            "required": True,
                            "weight": 0.1
                        }
                    ]
                },
                source="quality_standards"
            ),
            ObservationCreate(
                type="checklist_category",
                value={
                    "category": "Technical SEO",
                    "weight": 0.3,
                    "required_score": 0.85,
                    "checks": [
                        {
                            "item": "Title tag optimized (50-60 characters)",
                            "required": True,
                            "weight": 0.25
                        },
                        {
                            "item": "Meta description compelling (150-160 chars)",
                            "required": True,
                            "weight": 0.25
                        },
                        {
                            "item": "Headers properly structured (H1→H2→H3)",
                            "required": True,
                            "weight": 0.2
                        },
                        {
                            "item": "Images optimized with alt text",
                            "required": True,
                            "weight": 0.15
                        },
                        {
                            "item": "Internal/external links added",
                            "required": False,
                            "weight": 0.1
                        },
                        {
                            "item": "Schema markup implemented",
                            "required": False,
                            "weight": 0.05
                        }
                    ]
                },
                source="seo_requirements"
            ),
            ObservationCreate(
                type="checklist_category",
                value={
                    "category": "User Experience",
                    "weight": 0.3,
                    "required_score": 0.9,
                    "checks": [
                        {
                            "item": "Scannable with clear sections",
                            "required": True,
                            "weight": 0.3
                        },
                        {
                            "item": "Mobile-responsive formatting",
                            "required": True,
                            "weight": 0.25
                        },
                        {
                            "item": "Page loads in <3 seconds",
                            "required": True,
                            "weight": 0.2
                        },
                        {
                            "item": "No broken links or errors",
                            "required": True,
                            "weight": 0.15
                        },
                        {
                            "item": "Clear next steps for reader",
                            "required": True,
                            "weight": 0.1
                        }
                    ]
                },
                source="ux_standards"
            ),
            ObservationCreate(
                type="scoring_guide",
                value={
                    "overall_calculation": "weighted_average(categories)",
                    "passing_score": 0.85,
                    "excellence_score": 0.95,
                    "interpretation": {
                        "below_0.7": "Major revisions needed",
                        "0.7_to_0.85": "Minor improvements required",
                        "0.85_to_0.95": "Ready to publish",
                        "above_0.95": "Exceptional quality"
                    }
                },
                source="quality_standards"
            )
        ]
    )
    
    # Store the checklist
    try:
        checklist_result = await manager.create_entities(
            client_id=client_id,
            actor_type='synth_class',
            actor_id=str(synth_class_id),
            entities=[quality_checklist]
        )
        
        checklist_id = UUID(checklist_result[0]['id'])
        logger.info(f"✅ Created Quality Checklist with ID: {checklist_id}")
        
    except Exception as e:
        logger.error(f"❌ Error creating checklist: {e}")
    
    # Note: We cannot create a relation between them at synth_class level
    # due to current system limitations. Relations would need to be created
    # at the synth level when they use these templates.
    
    logger.info("\n📊 Summary:")
    logger.info(f"  - Blog SOP stored at synth_class level (ID: {synth_class_id})")
    logger.info(f"  - Quality Checklist stored at synth_class level")
    logger.info(f"  - Total observations: 6 in SOP, 4 in Checklist")
    logger.info("\n⚡ These procedures are now accessible to all synths of class 24")
    logger.info("   using hierarchical memory search!")
    
    # Close database connection
    db.close()

async def verify_hierarchical_access(
    # client_id removed - use actor_id when actor_type="client"
    synth_id: UUID,
    synth_class_id: int = 24
):
    """Verify that a synth can access the procedures through hierarchy"""
    
    # Get database session
    db = next(get_db())
    
    # Initialize services
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    
    manager = HierarchicalMemoryManager(db, embedding_service)
    
    logger.info(f"\n🔍 Verifying hierarchical access for synth {synth_id}")
    
    # Search without hierarchy (should find nothing)
    strict_results = await manager.search_nodes(
        client_id=client_id,
        actor_type='synth',
        actor_id=synth_id,
        query="blog writing SOP",
        include_hierarchy=False
    )
    
    logger.info(f"  Strict search: Found {len(strict_results)} results")
    
    # Search with hierarchy (should find procedures)
    hierarchical_results = await manager.search_hierarchical_memories(
        client_id=client_id,
        actor_type='synth',
        actor_id=synth_id,
        query="blog writing SOP",
        include_synth_class=True
    )
    
    logger.info(f"  Hierarchical search: Found {len(hierarchical_results)} results")
    
    for result in hierarchical_results:
        logger.info(f"    - {result['entity_name']} (from {result['access_source']})")
    
    db.close()

# Example usage
async def main():
    """Main function to run the storage script"""
    
    # Example IDs - replace with your actual values
    client_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    synth_id = UUID("660e8400-e29b-41d4-a716-446655440001")
    synth_class_id = 24
    
    # Store the procedures
    await store_blog_procedures(client_id, synth_class_id)
    
    # Verify access
    await verify_hierarchical_access(client_id, synth_id, synth_class_id)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Store blog procedures for synth_class 24")
    parser.add_argument("--client-id", type=str, required=True, help="Client UUID")
    parser.add_argument("--synth-id", type=str, help="Synth UUID for verification")
    parser.add_argument("--synth-class-id", type=int, default=24, help="Synth class ID")
    parser.add_argument("--verify-only", action="store_true", help="Only verify access")
    
    args = parser.parse_args()
    
    client_id = UUID(args.client_id)
    synth_class_id = args.synth_class_id
    
    if args.verify_only:
        if not args.synth_id:
            logger.info("❌ --synth-id required for verification")
            exit(1)
        synth_id = UUID(args.synth_id)
        asyncio.run(verify_hierarchical_access(client_id, synth_id, synth_class_id))
    else:
        asyncio.run(store_blog_procedures(client_id, synth_class_id))
        
        if args.synth_id:
            synth_id = UUID(args.synth_id)
            asyncio.run(verify_hierarchical_access(client_id, synth_id, synth_class_id))