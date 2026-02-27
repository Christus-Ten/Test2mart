import os
import random
import string
from flask import Flask, request, jsonify, render_template, abort
from models import db, Command

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Clé API pour l'upload (à changer en production)
UPLOAD_API_KEY = os.environ.get("UPLOAD_API_KEY", "secret-key-change-me")

def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@app.route('/')
def index():
    # Récupération des stats pour l'affichage initial
    total_commands = Command.query.count()
    total_likes = db.session.query(db.func.sum(Command.likes)).scalar() or 0
    total_shares = db.session.query(db.func.sum(Command.shares)).scalar() or 0
    # active_users simulé (0 pour l'instant)
    return render_template('index.html',
                           total_commands=total_commands,
                           total_likes=total_likes,
                           total_shares=total_shares)

# --- API Endpoints ---

@app.route('/api/items', methods=['GET'])
def list_items():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    filter_type = request.args.get('filter', '')  # trending, recent

    query = Command.query

    if search:
        query = query.filter(Command.name.contains(search) | Command.description.contains(search) | Command.author.contains(search))
    if category and category != "All Commands":
        query = query.filter_by(category=category)
    
    if filter_type == 'trending':
        query = query.order_by(Command.views.desc())
    elif filter_type == 'recent':
        query = query.order_by(Command.created_at.desc())
    else:
        query = query.order_by(Command.created_at.desc())

    total = query.count()
    items = query.paginate(page=page, per_page=limit, error_out=False)
    return jsonify({
        "items": [cmd.to_dict() for cmd in items.items],
        "total": total,
        "page": page,
        "totalPages": (total + limit - 1) // limit
    })

@app.route('/api/item/<int:item_id>', methods=['GET'])
def get_item(item_id):
    cmd = Command.query.get_or_404(item_id)
    cmd.views += 1
    db.session.commit()
    return jsonify(cmd.to_dict(include_code=True))

@app.route('/api/lookup/<identifier>', methods=['GET'])
def lookup_item(identifier):
    cmd = None
    if identifier.isdigit():
        cmd = Command.query.get(int(identifier))
    else:
        cmd = Command.query.filter_by(short_id=identifier).first()
    if not cmd:
        abort(404, description="Command not found")
    cmd.views += 1
    db.session.commit()
    return jsonify(cmd.to_dict(include_code=True))

@app.route('/raw/<identifier>', methods=['GET'])
def raw_code(identifier):
    cmd = None
    if identifier.isdigit():
        cmd = Command.query.get(int(identifier))
    else:
        cmd = Command.query.filter_by(short_id=identifier).first()
    if not cmd:
        abort(404, description="Command not found")
    return cmd.code, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/api/stats', methods=['GET'])
def stats():
    total_commands = Command.query.count()
    total_likes = db.session.query(db.func.sum(Command.likes)).scalar() or 0
    total_shares = db.session.query(db.func.sum(Command.shares)).scalar() or 0
    # active_users simulé
    return jsonify({
        "totalCommands": total_commands,
        "totalLikes": total_likes,
        "totalShares": total_shares,
        "activeUsers": 0
    })

@app.route('/api/items/<int:item_id>/like', methods=['POST'])
def like_item(item_id):
    cmd = Command.query.get_or_404(item_id)
    cmd.likes += 1
    db.session.commit()
    return jsonify({"likes": cmd.likes})

@app.route('/api/items/<int:item_id>/share', methods=['POST'])
def share_item(item_id):
    cmd = Command.query.get_or_404(item_id)
    cmd.shares += 1
    db.session.commit()
    return jsonify({"shares": cmd.shares})

@app.route('/api/items', methods=['POST'])
def upload_item():
    api_key = request.headers.get('X-API-Key')
    if api_key != UPLOAD_API_KEY:
        abort(403, description="Invalid API key")

    data = request.get_json()
    required = ['itemName', 'authorName', 'code']
    if not data or not all(k in data for k in required):
        abort(400, description="Missing required fields")

    # Vérifier si le nom existe déjà (optionnel)
    existing = Command.query.filter_by(name=data['itemName']).first()
    if existing:
        abort(409, description="A command with this name already exists")

    cmd = Command(
        short_id=generate_short_id(),
        name=data['itemName'],
        description=data.get('description', ''),
        author=data['authorName'],
        code=data['code'],
        category=data.get('category', 'GoatBot'),
        tags=','.join(data.get('tags', [])),
        difficulty=data.get('difficulty', 'Intermediate')
    )
    db.session.add(cmd)
    db.session.commit()

    return jsonify({
        "success": True,
        "itemId": cmd.id,
        "shortId": cmd.short_id,
        "message": "Upload successful"
    }), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Ajout de données de démo si la base est vide
        if Command.query.count() == 0:
            demo_commands = [
                Command(
                    short_id=generate_short_id(),
                    name="autodl",
                    description="Bot command from GoatBot.",
                    author="GoatBot Team",
                    code='// autodl code here',
                    category="GoatBot",
                    tags="goatbot,command",
                    difficulty="Intermediate",
                    views=15,
                    likes=3
                ),
                Command(
                    short_id=generate_short_id(),
                    name="aryan Chathan",
                    description="Bot command from GoatBot.",
                    author="Aryan",
                    code='// aryan code',
                    category="GoatBot",
                    tags="goatbot,command",
                    difficulty="Intermediate",
                    views=7,
                    likes=1
                ),
                Command(
                    short_id=generate_short_id(),
                    name="steal",
                    description="Bot command from GoatBot.",
                    author="Unknown",
                    code='// steal code',
                    category="GoatBot",
                    tags="goatbot,command",
                    difficulty="Intermediate",
                    views=23,
                    likes=5
                )
            ]
            db.session.add_all(demo_commands)
            db.session.commit()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
