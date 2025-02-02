from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from db.database import Dynamic


def get_all_dynamic_entries(db: Session):
    return db.query(Dynamic).all()

def add_to_dynamic(db: Session, analysis_id):
    dynamic_entry = Dynamic(analysis_id=analysis_id)
    db.add(dynamic_entry)
    db.commit()
    return dynamic_entry

def remove_from_dynamic(db: Session, analysis_id):
    dynamic_entry = db.query(Dynamic).filter_by(analysis_id=analysis_id).first()
    if dynamic_entry:
        db.delete(dynamic_entry)
        db.commit()
        return True
    return False