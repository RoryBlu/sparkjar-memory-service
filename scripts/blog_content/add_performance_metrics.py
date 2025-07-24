#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Add performance metrics entity to blog writing knowledge.
Captures target metrics and KPIs for blog content performance.
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

def add_performance_metrics():
    """Add performance metrics entity with target values"""
    
    logger.info("📊 Adding performance metrics to blog writing knowledge")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Constants for synth_class 24
        ACTOR_TYPE = 'synth_class'
        ACTOR_ID = '24'  # Text field storing the class ID
        
        # Create performance metrics entity
        metrics_entity = MemoryEntities(
            id=uuid4(),
            actor_type=ACTOR_TYPE,
            actor_id=ACTOR_ID,
            entity_name='Blog Performance Metrics Dashboard',
            entity_type='metrics_framework',
            metadata={
                'purpose': 'Track and optimize blog content performance',
                'frequency': 'weekly_review',
                'tool_integration': ['Google Analytics', 'Search Console', 'Social Media Analytics']
            }
        )
        
        db.add(metrics_entity)
        db.flush()  # Get the ID for relationships
        
        logger.info(f"✅ Created metrics entity with ID: {metrics_entity.id}")
        
        # Add engagement metrics observation
        engagement_metrics = MemoryObservations(
            id=uuid4(),
            entity_id=metrics_entity.id,
            observation_type='performance_target',
            observation_value={
                'category': 'Engagement Metrics',
                'metrics': [
                    {
                        'name': 'Average Time on Page',
                        'target': '4-6 minutes',
                        'minimum_acceptable': '2 minutes',
                        'calculation': 'Total time spent / Number of sessions',
                        'optimization_tips': [
                            'Use compelling introductions',
                            'Break content with subheadings',
                            'Add interactive elements',
                            'Include relevant images every 300 words'
                        ]
                    },
                    {
                        'name': 'Bounce Rate',
                        'target': '<40%',
                        'maximum_acceptable': '60%',
                        'calculation': 'Single page sessions / Total sessions',
                        'optimization_tips': [
                            'Improve page load speed',
                            'Match content to search intent',
                            'Add internal links to related content',
                            'Ensure mobile responsiveness'
                        ]
                    },
                    {
                        'name': 'Pages per Session',
                        'target': '2.5-3.5',
                        'minimum_acceptable': '1.8',
                        'calculation': 'Total page views / Total sessions',
                        'optimization_tips': [
                            'Create content clusters',
                            'Use clear CTAs for next articles',
                            'Implement related posts section',
                            'Build topic pillar pages'
                        ]
                    },
                    {
                        'name': 'Scroll Depth',
                        'target': '75% reach 50% of page',
                        'minimum_acceptable': '50% reach 50% of page',
                        'tracking_points': ['25%', '50%', '75%', '100%'],
                        'optimization_tips': [
                            'Front-load value proposition',
                            'Use bucket brigades',
                            'Add visual breaks',
                            'Optimize content length'
                        ]
                    }
                ]
            },
            source='industry_benchmarks_2024'
        )
        
        # Add conversion metrics observation
        conversion_metrics = MemoryObservations(
            id=uuid4(),
            entity_id=metrics_entity.id,
            observation_type='performance_target',
            observation_value={
                'category': 'Conversion Metrics',
                'metrics': [
                    {
                        'name': 'Email Signup Rate',
                        'target': '2-3%',
                        'minimum_acceptable': '1%',
                        'calculation': 'Email signups / Unique visitors',
                        'optimization_tips': [
                            'Offer content upgrades',
                            'Use exit-intent popups',
                            'Place opt-ins at high-engagement points',
                            'A/B test CTA copy'
                        ]
                    },
                    {
                        'name': 'Content Download Rate',
                        'target': '5-8%',
                        'minimum_acceptable': '3%',
                        'applies_to': 'Posts with downloadable resources',
                        'optimization_tips': [
                            'Create valuable lead magnets',
                            'Use compelling preview images',
                            'Highlight unique value',
                            'Minimize form fields'
                        ]
                    },
                    {
                        'name': 'Demo Request Rate',
                        'target': '0.5-1%',
                        'minimum_acceptable': '0.2%',
                        'applies_to': 'Bottom-funnel content',
                        'optimization_tips': [
                            'Include case studies',
                            'Show ROI clearly',
                            'Use social proof',
                            'Create urgency ethically'
                        ]
                    }
                ]
            },
            source='b2b_saas_benchmarks'
        )
        
        # Add social metrics observation
        social_metrics = MemoryObservations(
            id=uuid4(),
            entity_id=metrics_entity.id,
            observation_type='performance_target',
            observation_value={
                'category': 'Social Sharing Metrics',
                'metrics': [
                    {
                        'name': 'Social Share Rate',
                        'target': '1-2% of visitors',
                        'minimum_acceptable': '0.5%',
                        'platforms': ['LinkedIn', 'Twitter', 'Facebook'],
                        'optimization_tips': [
                            'Create tweetable quotes',
                            'Add social share buttons above fold',
                            'Use compelling social media cards',
                            'Include statistics and data'
                        ]
                    },
                    {
                        'name': 'LinkedIn Engagement Rate',
                        'target': '2-4%',
                        'calculation': '(Reactions + Comments + Shares) / Impressions',
                        'b2b_priority': 'HIGH',
                        'optimization_tips': [
                            'Post during business hours',
                            'Tag relevant people/companies',
                            'Ask thoughtful questions',
                            'Share key insights in post'
                        ]
                    },
                    {
                        'name': 'Comment-to-View Ratio',
                        'target': '0.5-1%',
                        'indicates': 'Content quality and engagement depth',
                        'optimization_tips': [
                            'End with open questions',
                            'Respond to all comments',
                            'Create controversial (ethical) takes',
                            'Invite expert opinions'
                        ]
                    }
                ]
            },
            source='social_media_benchmarks'
        )
        
        # Add SEO performance metrics
        seo_metrics = MemoryObservations(
            id=uuid4(),
            entity_id=metrics_entity.id,
            observation_type='performance_target',
            observation_value={
                'category': 'SEO Performance Metrics',
                'metrics': [
                    {
                        'name': 'Organic CTR',
                        'target_by_position': {
                            'position_1': '28-32%',
                            'position_2': '15-20%',
                            'position_3': '10-12%',
                            'position_4-10': '2-8%'
                        },
                        'optimization_tips': [
                            'Optimize meta titles for clicks',
                            'Use numbers in titles',
                            'Include year for freshness',
                            'Match search intent precisely'
                        ]
                    },
                    {
                        'name': 'Page Load Speed',
                        'target': '<2.5 seconds',
                        'maximum_acceptable': '3 seconds',
                        'core_web_vitals': {
                            'LCP': '<2.5s',
                            'FID': '<100ms',
                            'CLS': '<0.1'
                        },
                        'impact': '1 second delay = 7% conversion loss'
                    },
                    {
                        'name': 'Keyword Rankings Growth',
                        'target': '10-15% quarterly improvement',
                        'tracking': {
                            'primary_keywords': 'Top 3 positions',
                            'secondary_keywords': 'Top 10 positions',
                            'long_tail': 'Top 20 positions'
                        }
                    },
                    {
                        'name': 'Backlink Acquisition',
                        'target': '5-10 quality backlinks per post',
                        'quality_indicators': ['DA>40', 'Relevant niche', 'Editorial link'],
                        'outreach_conversion': '5-10% success rate'
                    }
                ]
            },
            source='seo_industry_standards'
        )
        
        # Add content quality scores
        quality_metrics = MemoryObservations(
            id=uuid4(),
            entity_id=metrics_entity.id,
            observation_type='performance_target',
            observation_value={
                'category': 'Content Quality Scores',
                'metrics': [
                    {
                        'name': 'Readability Score',
                        'target': 'Flesch 60-70',
                        'grade_level': '8th-10th grade',
                        'tools': ['Hemingway Editor', 'Grammarly'],
                        'factors': [
                            'Sentence length <20 words avg',
                            'Paragraph length <150 words',
                            'Active voice >80%',
                            'Transition words >30%'
                        ]
                    },
                    {
                        'name': 'E-A-T Score',
                        'components': {
                            'expertise': 'Author bio, credentials, experience',
                            'authoritativeness': 'Citations, backlinks, mentions',
                            'trustworthiness': 'Fact-checking, sources, transparency'
                        },
                        'optimization': [
                            'Include author bios',
                            'Link to authoritative sources',
                            'Update content regularly',
                            'Display credentials prominently'
                        ]
                    },
                    {
                        'name': 'Content Depth Score',
                        'target': '>2000 words for pillar content',
                        'comprehensiveness': [
                            'Covers all user questions',
                            'Includes examples/case studies',
                            'Provides actionable takeaways',
                            'Addresses objections'
                        ]
                    }
                ]
            },
            source='content_marketing_institute'
        )
        
        # Add all observations
        observations = [engagement_metrics, conversion_metrics, social_metrics, seo_metrics, quality_metrics]
        for obs in observations:
            db.add(obs)
            logger.info(f"  - Added {obs.observation_value.get('category', 'observation')}")
        
        db.commit()
        logger.info("✅ Successfully added performance metrics entity and observations")
        
        # Verify the addition
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM memory_observations
            WHERE entity_id = :entity_id
        """), {"entity_id": metrics_entity.id})
        
        count = result.scalar()
        logger.info(f"📊 Total observations for Performance Metrics: {count}")
        
    except Exception as e:
        logger.error(f"❌ Error adding performance metrics: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_performance_metrics()