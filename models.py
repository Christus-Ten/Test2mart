from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Command(db.Model):
    __tablename__ = 'commands'
    id = db.Column(db.Integer, primary_key=True)
    short_id = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    author = db.Column(db.String(100), nullable=False)
    code = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="GoatBot")  # GoatBot, MiraiBot, AutoBot
    tags = db.Column(db.String(200), default="")
    difficulty = db.Column(db.String(50), default="Intermediate")
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)   # pour "TOTAL SHARES"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, include_code=False):
        data = {
            "itemID": self.id,
            "shortId": self.short_id,
            "itemName": self.name,
            "description": self.description,
            "authorName": self.author,
            "category": self.category,
            "tags": self.tags.split(",") if self.tags else [],
            "difficulty": self.difficulty,
            "views": self.views,
            "likes": self.likes,
            "shares": self.shares,
            "createdAt": self.created_at.isoformat(),
            "rawLink": f"/raw/{self.short_id}"
        }
        if include_code:
            data["code"] = self.code
        return data
