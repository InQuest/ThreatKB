from app import db

class Tags(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key = True)
    
    text = db.Column(db.String(256))
    

    def to_dict(self):
        return dict(
            text = self.text,
            id = self.id
        )

    def __repr__(self):
        return '<Tags %r>' % (self.id)
