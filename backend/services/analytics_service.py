from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.models import Document

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview_metrics(self):
        total_records = self.db.query(Document).count()
        total_schemes = self.db.query(Document.scheme).distinct().count()
        total_states = self.db.query(Document.state).filter(Document.state != 'Unknown', Document.state != None).distinct().count()
        total_districts = self.db.query(Document.district).filter(Document.district != 'Unknown', Document.district != None).distinct().count()
        
        gap_signals = self.db.query(Document).filter(func.lower(Document.awareness_gap) == 'yes').count()
        
        return {
            "total_records": total_records,
            "schemes_analyzed": total_schemes,
            "states_covered": total_states,
            "districts_covered": total_districts,
            "awareness_gap_signals": gap_signals,
            "gap_rate": round(gap_signals / total_records * 100, 2) if total_records > 0 else 0
        }
        
    def get_scheme_metrics(self):
        results = self.db.query(
            Document.scheme,
            func.count(Document.id).label('total'),
            func.sum(
                func.cast(func.lower(Document.awareness_gap) == 'yes', func.Integer())
            ).label('gaps')
        ).group_by(Document.scheme).all()
        
        return [
            {
                "scheme": r[0],
                "total_records": r[1],
                "gap_signals": r[2],
                "gap_rate": round(r[2] / r[1] * 100, 2) if r[1] > 0 else 0
            }
            for r in results
        ]

    def get_geographic_metrics(self):
        # State level aggregation
        results = self.db.query(
            Document.state,
            func.count(Document.id).label('total'),
            func.sum(
                func.cast(func.lower(Document.awareness_gap) == 'yes', func.Integer())
            ).label('gaps')
        ).filter(Document.state != None, Document.state != 'Unknown').group_by(Document.state).all()
        
        return [
            {
                "state": r[0],
                "total_records": r[1],
                "gap_signals": r[2],
                "gap_rate": round(r[2] / r[1] * 100, 2) if r[1] > 0 else 0
            }
            for r in results
        ]
