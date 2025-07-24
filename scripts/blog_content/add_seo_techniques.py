#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Add comprehensive SEO techniques to blog writing knowledge.
Expands the existing SEO knowledge base with detailed optimization strategies.
"""
import os
import sys
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
# Add crew-api path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from crew-api models
from services.crew_api.src.database.models import MemoryEntities, MemoryObservations
from sparkjar_crew.shared.config.config import DATABASE_URL_DIRECT

# Create synchronous engine for this script
engine = create_engine(DATABASE_URL_DIRECT.replace('postgresql+asyncpg', 'postgresql'))
SessionLocal = sessionmaker(bind=engine)

def add_seo_techniques():
    """Add comprehensive SEO techniques to existing SEO knowledge base"""
    
    logger.info("🔍 Adding comprehensive SEO techniques to blog writing knowledge")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Constants for synth_class 24
        ACTOR_TYPE = 'synth_class'
        ACTOR_ID = '24'  # Text field storing the class ID
        
        # First, find the SEO Knowledge Base entity
        result = db.execute(text("""
            SELECT id, entity_name 
            FROM memory_entities
            WHERE actor_type = :actor_type
            AND actor_id = :actor_id
            AND entity_name LIKE '%SEO Best Practices%'
            LIMIT 1
        """), {"actor_type": ACTOR_TYPE, "actor_id": ACTOR_ID})
        
        seo_entity = result.fetchone()
        if not seo_entity:
            logger.info("❌ SEO Knowledge Base not found!")
            return
        
        seo_entity_id = seo_entity[0]
        logger.info(f"✅ Found SEO entity: {seo_entity[1]}")
        
        # Add keyword density optimization
        keyword_density = MemoryObservations(
            id=uuid4(),
            entity_id=seo_entity_id,
            observation_type='seo_technique',
            observation_value={
                'technique': 'Keyword Density Optimization',
                'category': 'on_page_seo',
                'description': 'Strategic keyword placement for optimal search visibility',
                'guidelines': {
                    'primary_keyword': {
                        'density': '1-2%',
                        'placements': [
                            'Title tag (preferably at beginning)',
                            'First 100 words of content',
                            'One H2 subheading',
                            'Meta description',
                            'URL slug',
                            'Image alt text (at least one)',
                            'Last paragraph'
                        ],
                        'avoid': 'Keyword stuffing (>3% density)'
                    },
                    'secondary_keywords': {
                        'density': '0.5-1%',
                        'usage': '2-3 variations throughout content',
                        'placements': ['Subheadings', 'Body paragraphs', 'Image captions']
                    },
                    'lsi_keywords': {
                        'purpose': 'Semantic relevance signals',
                        'usage': 'Natural integration throughout',
                        'sources': ['Google autocomplete', 'Related searches', 'Answer the Public']
                    }
                },
                'tools': ['Yoast SEO', 'Surfer SEO', 'Clearscope'],
                'example': {
                    'primary': 'content marketing strategy',
                    'secondary': ['content marketing plan', 'content strategy framework'],
                    'lsi': ['editorial calendar', 'content audit', 'buyer personas']
                }
            },
            source='seo_best_practices_2024'
        )
        
        # Add meta optimization techniques
        meta_optimization = MemoryObservations(
            id=uuid4(),
            entity_id=seo_entity_id,
            observation_type='seo_technique',
            observation_value={
                'technique': 'Meta Tag Optimization',
                'category': 'on_page_seo',
                'description': 'Crafting compelling meta elements for SERP performance',
                'components': {
                    'title_tag': {
                        'length': '50-60 characters',
                        'structure': '[Primary Keyword] - [Secondary/Benefit] | [Brand]',
                        'tips': [
                            'Front-load primary keyword',
                            'Include emotional triggers or numbers',
                            'Create curiosity gap',
                            'Avoid keyword stuffing',
                            'Make each title unique'
                        ],
                        'examples': [
                            'Content Marketing Strategy: 7 Steps to 10x Your Traffic | Brand',
                            'How to Create Viral Content in 2024 (Data-Driven Guide) | Brand'
                        ]
                    },
                    'meta_description': {
                        'length': '150-160 characters',
                        'structure': 'Hook + Value proposition + CTA',
                        'components': [
                            'Include primary keyword naturally',
                            'Address search intent directly',
                            'Include unique value proposition',
                            'Add subtle call-to-action',
                            'Use active voice'
                        ],
                        'power_words': ['Discover', 'Learn', 'Master', 'Proven', 'Ultimate'],
                        'example': 'Discover the proven content marketing strategy that helped us grow organic traffic by 312%. Learn our exact framework and get free templates. Start today →'
                    },
                    'open_graph_tags': {
                        'og_title': 'Can be longer than title tag (up to 88 chars)',
                        'og_description': 'Up to 200 characters for social sharing',
                        'og_image': 'Minimum 1200x630px, text overlay for context',
                        'og_type': 'article for blog posts'
                    }
                }
            },
            source='moz_seo_guide_2024'
        )
        
        # Add link building strategies
        link_building = MemoryObservations(
            id=uuid4(),
            entity_id=seo_entity_id,
            observation_type='seo_technique',
            observation_value={
                'technique': 'Strategic Link Building',
                'category': 'off_page_seo',
                'description': 'Building authority through quality backlinks and internal linking',
                'strategies': {
                    'internal_linking': {
                        'guidelines': [
                            '3-5 internal links per 1000 words',
                            'Use descriptive anchor text (not "click here")',
                            'Link to relevant pillar pages',
                            'Create topic clusters',
                            'Distribute link equity strategically'
                        ],
                        'structure': {
                            'hub_pages': 'Main topic pages (link to all related content)',
                            'spoke_pages': 'Detailed subtopic pages (link back to hub)',
                            'navigation': 'Contextual links between related topics'
                        }
                    },
                    'external_linking': {
                        'outbound': {
                            'quantity': '2-4 per article',
                            'quality': 'High-authority sources only (DA>50)',
                            'purpose': 'Support claims with data',
                            'attributes': 'Use rel="nofollow" for affiliate links'
                        },
                        'link_earning': {
                            'linkable_assets': [
                                'Original research/surveys',
                                'Comprehensive guides (>3000 words)',
                                'Free tools/calculators',
                                'Infographics with embed code',
                                'Industry reports with data'
                            ],
                            'outreach_templates': {
                                'broken_link': 'Found broken link → suggest replacement',
                                'resource_page': 'Suggest addition to curated lists',
                                'guest_post': 'Offer unique insights for their audience',
                                'expert_roundup': 'Contribute to or create compilations'
                            }
                        }
                    }
                },
                'metrics': {
                    'domain_authority': 'Target sites with DA>40',
                    'relevance': 'Topical relevance > high DA irrelevant site',
                    'anchor_text_distribution': {
                        'branded': '40%',
                        'naked_url': '20%',
                        'exact_match': '10%',
                        'partial_match': '20%',
                        'generic': '10%'
                    }
                }
            },
            source='backlinko_link_building_guide'
        )
        
        # Add technical SEO checklist
        technical_seo = MemoryObservations(
            id=uuid4(),
            entity_id=seo_entity_id,
            observation_type='seo_technique',
            observation_value={
                'technique': 'Technical SEO Optimization',
                'category': 'technical_seo',
                'description': 'Backend optimizations for crawlability and indexation',
                'checklist': {
                    'url_structure': {
                        'format': 'domain.com/category/keyword-rich-slug',
                        'rules': [
                            'Use hyphens, not underscores',
                            'Keep URLs under 60 characters',
                            'Include target keyword',
                            'Avoid stop words when possible',
                            'Use lowercase only'
                        ]
                    },
                    'schema_markup': {
                        'types': ['Article', 'BlogPosting', 'HowTo', 'FAQPage'],
                        'benefits': 'Rich snippets, better CTR',
                        'implementation': 'JSON-LD in <head> section',
                        'testing': 'Google Rich Results Test tool'
                    },
                    'page_speed': {
                        'targets': {
                            'mobile': '<3 seconds',
                            'desktop': '<2 seconds'
                        },
                        'optimizations': [
                            'Compress images (WebP format)',
                            'Lazy load below-fold content',
                            'Minify CSS/JS',
                            'Enable browser caching',
                            'Use CDN for assets'
                        ]
                    },
                    'mobile_optimization': {
                        'viewport': 'Responsive design required',
                        'font_size': 'Minimum 16px for body text',
                        'tap_targets': 'Minimum 48x48px',
                        'above_fold': 'Critical content without scrolling'
                    }
                }
            },
            source='google_seo_documentation'
        )
        
        # Add content optimization workflow
        content_optimization = MemoryObservations(
            id=uuid4(),
            entity_id=seo_entity_id,
            observation_type='seo_technique',
            observation_value={
                'technique': 'Content Optimization Workflow',
                'category': 'content_seo',
                'description': 'Step-by-step process for SEO-optimized content creation',
                'workflow': [
                    {
                        'step': 1,
                        'name': 'Keyword Research',
                        'actions': [
                            'Identify primary keyword (search volume >1000)',
                            'Find 3-5 secondary keywords',
                            'Analyze search intent (informational/transactional)',
                            'Check keyword difficulty (<40 for new sites)',
                            'Study SERP features (snippets, PAA, videos)'
                        ],
                        'tools': ['Ahrefs', 'SEMrush', 'Google Keyword Planner']
                    },
                    {
                        'step': 2,
                        'name': 'Competitive Analysis',
                        'actions': [
                            'Analyze top 10 ranking pages',
                            'Identify content gaps',
                            'Note average word count',
                            'Study heading structure',
                            'Find link opportunities'
                        ]
                    },
                    {
                        'step': 3,
                        'name': 'Content Creation',
                        'actions': [
                            'Create comprehensive outline',
                            'Write 20% more than competitors',
                            'Include multimedia elements',
                            'Add unique insights/data',
                            'Optimize for featured snippets'
                        ]
                    },
                    {
                        'step': 4,
                        'name': 'On-Page Optimization',
                        'actions': [
                            'Optimize title and meta description',
                            'Structure with H2/H3 tags',
                            'Add internal/external links',
                            'Optimize images (compress, alt text)',
                            'Implement schema markup'
                        ]
                    },
                    {
                        'step': 5,
                        'name': 'Post-Publish',
                        'actions': [
                            'Submit to Google Search Console',
                            'Share on social media',
                            'Start outreach for backlinks',
                            'Monitor rankings weekly',
                            'Update quarterly with fresh data'
                        ]
                    }
                ]
            },
            source='seo_content_playbook_2024'
        )
        
        # Add all observations
        observations = [keyword_density, meta_optimization, link_building, technical_seo, content_optimization]
        for obs in observations:
            db.add(obs)
            technique_name = obs.observation_value.get('technique', 'SEO technique')
            logger.info(f"  - Added {technique_name}")
        
        db.commit()
        logger.info("✅ Successfully added comprehensive SEO techniques")
        
        # Verify the addition
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM memory_observations
            WHERE entity_id = :entity_id
            AND observation_type = 'seo_technique'
        """), {"entity_id": seo_entity_id})
        
        count = result.scalar()
        logger.info(f"📊 Total SEO technique observations: {count}")
        
    except Exception as e:
        logger.error(f"❌ Error adding SEO techniques: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_seo_techniques()