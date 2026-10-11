import time
import logging
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
from backend.app.models.crawl import CollectionCampaign, CrawlUrl
from backend.app.services.crawl_engine import CollectionOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("worker")

def process_campaigns(db: Session, orchestrator: CollectionOrchestrator):
    """Finds pending campaigns and discovers URLs for them."""
    pending_campaigns = db.query(CollectionCampaign).filter(
        CollectionCampaign.status == 'pending'
    ).all()
    
    for campaign in pending_campaigns:
        logger.info(f"Starting discovery for campaign: {campaign.name}")
        try:
            # We don't run the whole run_campaign synchronously. 
            # We will split it into discovery and then let the crawl loop handle the rest.
            
            # Start discovery phase
            campaign.status = 'discovering'
            db.commit()
            
            discovery_stats = orchestrator._discover_urls(campaign)
            
            # After discovery, set to collecting so the crawl loop can pick up its urls
            campaign.status = 'collecting'
            campaign.urls_discovered = discovery_stats.get('discovered', 0)
            campaign.urls_accepted = discovery_stats.get('accepted', 0)
            db.commit()
            
            logger.info(f"Discovery complete for {campaign.name}: {campaign.urls_accepted} URLs accepted.")
        except Exception as e:
            logger.error(f"Error in discovery for campaign {campaign.id}: {e}")
            campaign.status = 'failed'
            db.commit()

def process_crawl_urls(db: Session, orchestrator: CollectionOrchestrator):
    """Finds queued URLs and crawls them."""
    # Process up to 10 at a time
    urls = db.query(CrawlUrl).filter(
        CrawlUrl.status == 'queued'
    ).limit(10).all()
    
    if not urls:
        return False
        
    for url in urls:
        logger.info(f"Crawling URL: {url.url}")
        campaign = db.query(CollectionCampaign).filter(CollectionCampaign.id == url.campaign_id).first()
        try:
            # Process a single page
            # Note: _process_page needs to exist or we just use _collect_pages logic
            orchestrator._collect_pages(campaign) # Wait, this collects ALL urls for a campaign synchronously
            
            # Since orchestrator._collect_pages loops over all URLs for the campaign, 
            # it might be better to just let orchestrator._collect_pages run if we find collecting campaigns!
            
        except Exception as e:
            logger.error(f"Error crawling {url.url}: {e}")
            
    return True

def process_collecting_campaigns(db: Session, orchestrator: CollectionOrchestrator):
    """Finds campaigns in collecting state and runs the collect phase."""
    campaigns = db.query(CollectionCampaign).filter(
        CollectionCampaign.status == 'collecting'
    ).all()
    
    for campaign in campaigns:
        # Check if there are any pending urls left
        pending = db.query(CrawlUrl).filter(
            CrawlUrl.campaign_id == campaign.id,
            CrawlUrl.status.in_(['queued', 'retrying'])
        ).count()
        
        if pending == 0:
            logger.info(f"Campaign {campaign.id} is complete.")
            campaign.status = 'completed'
            db.commit()
            continue
            
        logger.info(f"Continuing collection for campaign: {campaign.name} ({pending} urls left)")
        try:
            # this processes URLs in batches
            orchestrator._collect_pages(campaign)
        except Exception as e:
            logger.error(f"Error collecting for campaign {campaign.id}: {e}")

def run_auto_pilot(db: Session, orchestrator: CollectionOrchestrator):
    import os
    if not os.path.exists(".autopilot"):
        return
        
    active = db.query(CollectionCampaign).filter(
        CollectionCampaign.status.in_(['pending', 'discovering', 'collecting'])
    ).count()
    
    if active > 0:
        return # wait for current campaigns to finish
        
    # Check if the last campaign finished recently (prevent spam)
    last_campaign = db.query(CollectionCampaign).order_by(CollectionCampaign.id.desc()).first()
    if last_campaign and last_campaign.status == 'completed' and last_campaign.finished_at:
        import datetime
        time_since = (datetime.datetime.utcnow() - last_campaign.finished_at).total_seconds()
        if time_since < 300: # Wait 5 minutes between auto-pilot runs
            return
            
    logger.info("Auto-Pilot Triggered: Spawning new collection campaign...")
    import datetime
    orchestrator.create_campaign(
        name=f"Auto-pilot {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        schemes=None,
        max_urls=1000,
        max_depth=2,
        max_pages_per_source=50
    )


def run_worker():
    logger.info("Starting Collection Worker...")
    Base.metadata.create_all(bind=engine)
    
    while True:
        db = SessionLocal()
        try:
            orchestrator = CollectionOrchestrator(db)
            
            # Step 1: Auto-pilot
            run_auto_pilot(db, orchestrator)
            
            # Step 2: Discover URLs for pending campaigns
            process_campaigns(db, orchestrator)
            
            # Step 3: Collect pages for collecting campaigns
            process_collecting_campaigns(db, orchestrator)
            
        except Exception as e:
            logger.error(f"Worker iteration error: {e}")
        finally:
            db.close()
            
        # Sleep to prevent high CPU usage
        time.sleep(5)

if __name__ == "__main__":
    run_worker()
