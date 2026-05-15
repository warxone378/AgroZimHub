from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Listing, Bid, InsuranceContract
from config import PROVINCES, SEED_TYPES, SOIL_TYPES, SECRET_KEY
from services.ai_engine import AIEngine
from services.weather_service import WeatherService
from functools import wraps
from datetime import datetime
import json, os, time

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrozim.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        phone = request.form['phone']
        province = request.form['province']
        if User.query.filter_by(username=username).first():
            flash('Username taken.', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, role=role, phone_number=phone, location_province=province)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', provinces=PROVINCES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/predictor', methods=['GET', 'POST'])
@login_required
def predictor():
    recommendation = None
    if request.method == 'POST':
        province = request.form['province']
        seed_type = request.form['seed_type']
        hectares = float(request.form['hectares'])
        soil_type = request.form['soil_type']
        soil_ph = float(request.form['soil_ph'])
        recommendation = AIEngine.predict_planting_strategy(province, seed_type, hectares, soil_type, soil_ph)
    return render_template('predictor.html', provinces=PROVINCES, seed_types=SEED_TYPES, soil_types=SOIL_TYPES, recommendation=recommendation)

@app.route('/marketplace')
def marketplace():
    query = Listing.query
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    if search:
        query = query.filter(Listing.title.contains(search) | Listing.crop_type.contains(search))
    if location:
        query = query.filter_by(location_province=location)
    listings = query.order_by(Listing.created_at.desc()).all()
    return render_template('marketplace.html', listings=listings, provinces=PROVINCES)

@app.route('/listing/new', methods=['GET', 'POST'])
@login_required
def create_listing():
    if request.method == 'POST':
        listing = Listing(
            title=request.form['title'],
            crop_type=request.form['crop_type'],
            quantity_kg=float(request.form['quantity']),
            price_per_kg=float(request.form['price']),
            location_province=request.form['location'],
            description=request.form.get('description', ''),
            seller_id=session['user_id']
        )
        db.session.add(listing)
        db.session.commit()
        flash('Listing created!', 'success')
        return redirect(url_for('marketplace'))
    return render_template('marketplace_form.html', provinces=PROVINCES)

@app.route('/listing/<int:id>')
def view_listing(id):
    listing = Listing.query.get_or_404(id)
    listing.view_count += 1
    db.session.commit()
    seller = User.query.get(listing.seller_id)
    return render_template('listing_detail.html', listing=listing, seller=seller)

@app.route('/listing/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_listing(id):
    listing = Listing.query.get_or_404(id)
    if listing.seller_id != session['user_id']:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('marketplace'))
    if request.method == 'POST':
        listing.title = request.form['title']
        listing.crop_type = request.form['crop_type']
        listing.quantity_kg = float(request.form['quantity'])
        listing.price_per_kg = float(request.form['price'])
        listing.location_province = request.form['location']
        listing.description = request.form.get('description', '')
        db.session.commit()
        flash('Listing updated!', 'success')
        return redirect(url_for('view_listing', id=listing.id))
    return render_template('marketplace_form.html', listing=listing, provinces=PROVINCES)

@app.route('/listing/<int:id>/delete', methods=['POST'])
@login_required
def delete_listing(id):
    listing = Listing.query.get_or_404(id)
    if listing.seller_id == session['user_id']:
        db.session.delete(listing)
        db.session.commit()
        flash('Listing deleted.', 'success')
    else:
        flash('Unauthorized.', 'danger')
    return redirect(url_for('marketplace'))

@app.route('/warnings')
@login_required
def warnings():
    user = User.query.get(session['user_id'])
    from config import PROVINCE_CITY
    city = PROVINCE_CITY.get(user.location_province, 'Harare,ZW')
    weather = WeatherService.get_weather_data(city)
    risk = WeatherService.analyze_weather_risks(weather)
    return render_template('warnings.html', risk_analysis=risk)

@app.route('/agronomists')
def agronomists():
    agros = User.query.filter_by(role='Agronomist').all()
    return render_template('agronomists.html', agronomists=agros)

# ---------- ENTERPRISE ROUTES ----------
@app.template_filter('usd_to_zig')
def usd_to_zig_filter(amount):
    from services.fintech_logic import FintechLogic
    return FintechLogic.usd_to_zig(amount)

@app.route('/place_bid/<int:listing_id>', methods=['POST'])
@login_required
def place_bid(listing_id):
    from services.fintech_logic import FintechLogic
    listing = Listing.query.get_or_404(listing_id)
    if session['role'] != 'Buyer':
        flash('Only buyers can bid.', 'danger')
        return redirect(url_for('marketplace'))
    bid_amount = float(request.form['bid_amount'])
    quantity = float(request.form['quantity_kg'])
    highest = Bid.query.filter_by(listing_id=listing_id).order_by(Bid.bid_amount_usd.desc()).first()
    if highest and bid_amount <= highest.bid_amount_usd:
        flash('Your bid must be higher than current highest.', 'warning')
        return redirect(url_for('marketplace'))
    bid = Bid(
        listing_id=listing_id,
        buyer_id=session['user_id'],
        bid_amount_usd=bid_amount,
        bid_amount_zig=FintechLogic.usd_to_zig(bid_amount),
        quantity_kg=quantity
    )
    db.session.add(bid)
    db.session.commit()
    flash('Bid placed successfully!', 'success')
    return redirect(url_for('marketplace'))

@app.route('/insurance')
@login_required
def insurance_dashboard():
    contracts = InsuranceContract.query.filter_by(farmer_id=session['user_id']).all()
    return render_template('insurance.html', contracts=contracts)

@app.route('/buy_insurance', methods=['POST'])
@login_required
def buy_insurance():
    trigger = request.form['trigger_type']
    threshold = float(request.form['threshold'])
    payout = float(request.form['payout'])
    premium = payout * 0.05
    contract = InsuranceContract(
        farmer_id=session['user_id'],
        trigger_type=trigger,
        threshold=threshold,
        premium_usd=premium,
        payout_usd=payout
    )
    db.session.add(contract)
    db.session.commit()
    flash(f'Insurance bought! Premium: ${premium:.2f}', 'success')
    return redirect(url_for('insurance_dashboard'))

@app.route('/check_insurance_triggers')
@login_required
def check_insurance_triggers():
    from services.weather_service import WeatherService
    from services.fintech_logic import ParametricInsurance
    from config import PROVINCE_CITY
    user = User.query.get(session['user_id'])
    city = PROVINCE_CITY.get(user.location_province, 'Harare,ZW')
    weather = WeatherService.get_weather_data(city)
    if not weather:
        flash('Weather data unavailable.', 'warning')
        return redirect(url_for('insurance_dashboard'))
    contracts = InsuranceContract.query.filter_by(farmer_id=session['user_id'], is_active=True, payout_made=False).all()
    triggered_count = 0
    for c in contracts:
        triggered, payout = ParametricInsurance.check_trigger(weather, {
            'trigger_type': c.trigger_type,
            'threshold': c.threshold,
            'payout_usd': c.payout_usd
        })
        if triggered:
            c.is_active = False
            c.triggered_at = datetime.utcnow()
            c.payout_made = True
            triggered_count += 1
    db.session.commit()
    flash(f'{triggered_count} insurance policies triggered.', 'info')
    return redirect(url_for('insurance_dashboard'))

@app.route('/ledger')
def ledger():
    return render_template('ledger.html')

@app.route('/verify_batch', methods=['POST'])
def verify_batch():
    from services.supply_chain import SupplyChainLedger
    batch_id = request.form['batch_id']
    result = SupplyChainLedger.verify_batch(batch_id)
    return render_template('ledger.html', result=result)

@app.route('/input_matcher', methods=['GET', 'POST'])
def input_matcher():
    matches = None
    if request.method == 'POST':
        from services.supply_chain import InputMatcher
        crop = request.form['crop_type']
        kg = float(request.form['required_kg'])
        matches = InputMatcher.match_requirements(crop, kg)
    return render_template('input_matcher.html', matches=matches)

@app.route('/silo_dashboard')
def silo_dashboard():
    from services.supply_chain import SmartSilo
    silo_data = SmartSilo.get_status()
    return render_template('silo_dashboard.html', silo_data=silo_data)

# ---------- NEW PAGES: CHAT, DISEASE, SMS, PRICES, FORUM ----------
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/chat_api', methods=['POST'])
@login_required
def chat_api():
    import requests
    from config import GEMINI_API_KEY
    data = request.get_json()
    question = data.get('question', '')
    prompt = f"You are a Zimbabwean agricultural expert. Answer this farmer's question concisely (max 150 words): {question}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 300}}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            answer = resp.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            answer = "Sorry, AI service is busy. Please try again later."
    except:
        answer = "Unable to connect to AI service."
    return {'answer': answer}

@app.route('/disease', methods=['GET', 'POST'])
@login_required
def disease_detector():
    result = None
    if request.method == 'POST':
        result = {
            'disease': 'Northern Leaf Blight (simulated)',
            'confidence': 87,
            'treatment': 'Apply fungicide containing azoxystrobin. Remove infected leaves.'
        }
    return render_template('disease.html', result=result)

@app.route('/sms', methods=['GET', 'POST'])
@login_required
def sms_alerts():
    status = None
    if request.method == 'POST':
        phone = request.form['phone']
        msg = request.form['message']
        status = f"Simulated SMS sent to {phone}: {msg[:50]}..."
    return render_template('sms.html', status=status)

@app.route('/prices')
@login_required
def market_prices():
    prices = [
        ('Maize', 0.45, '▲ +2%'),
        ('Wheat', 0.52, '▼ -1%'),
        ('Soybean', 0.68, '▲ +3%'),
        ('Groundnut', 1.20, 'stable'),
        ('Cotton', 0.85, '▲ +5%'),
    ]
    return render_template('prices.html', prices=prices)

# Forum data setup
FORUM_FILE = 'data/forum_posts.json'
def load_forum():
    if os.path.exists(FORUM_FILE):
        with open(FORUM_FILE) as f:
            return json.load(f)
    return {'posts': [], 'replies': {}}
def save_forum(data):
    with open(FORUM_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/forum')
def forum():
    data = load_forum()
    posts = sorted(data['posts'], key=lambda x: x.get('date', ''), reverse=True)
    return render_template('forum.html', posts=posts)

@app.route('/forum/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        data = load_forum()
        new_id = len(data['posts']) + 1
        post = {
            'id': new_id,
            'title': request.form['title'],
            'content': request.form['content'],
            'author': session['username'],
            'date': time.strftime('%Y-%m-%d %H:%M')
        }
        data['posts'].append(post)
        data['replies'][str(new_id)] = []
        save_forum(data)
        flash('Post created!', 'success')
        return redirect(url_for('forum'))
    return render_template('post_form.html')

@app.route('/forum/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    data = load_forum()
    post = next((p for p in data['posts'] if p['id'] == post_id), None)
    if not post:
        flash('Post not found', 'danger')
        return redirect(url_for('forum'))
    replies = data['replies'].get(str(post_id), [])
    if request.method == 'POST' and session.get('user_id'):
        reply = {
            'author': session['username'],
            'content': request.form['reply'],
            'date': time.strftime('%Y-%m-%d %H:%M')
        }
        data['replies'][str(post_id)].append(reply)
        save_forum(data)
        flash('Reply added', 'success')
        return redirect(url_for('view_post', post_id=post_id))
    return render_template('post_detail.html', post=post, replies=replies)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# ---------- PASSWORD RESET ----------
from auth_helpers import generate_reset_token, verify_reset_token, delete_token

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        # For simplicity, we treat username as email
        user = User.query.filter_by(username=email).first()
        if user:
            token = generate_reset_token(user.id)
            # In production, send email. Here print to console.
            reset_link = f"http://localhost:5000/reset_password/{token}"
            print(f"🔐 Password reset link for {user.username}: {reset_link}")
            flash('Reset link has been sent to your console (check Termux).', 'info')
        else:
            flash('No account with that username/email.', 'danger')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_id = verify_reset_token(token)
    if not user_id:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if request.method == 'POST':
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            user.set_password(password)
            db.session.commit()
            delete_token(token)
            flash('Password reset successfully. Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

# ---------- SHOPPING CART ----------
@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    items = []
    total = 0.0
    for listing_id, qty in cart_items.items():
        listing = Listing.query.get(int(listing_id))
        if listing:
            subtotal = listing.price_per_kg * qty
            items.append({'listing': listing, 'quantity': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template('cart.html', items=items, total=total)

@app.route('/add_to_cart/<int:listing_id>', methods=['POST'])
def add_to_cart(listing_id):
    qty = float(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[str(listing_id)] = cart.get(str(listing_id), 0) + qty
    session['cart'] = cart
    flash('Added to cart.', 'success')
    return redirect(request.referrer or url_for('marketplace'))

@app.route('/remove_from_cart/<int:listing_id>')
def remove_from_cart(listing_id):
    cart = session.get('cart', {})
    cart.pop(str(listing_id), None)
    session['cart'] = cart
    flash('Removed from cart.', 'info')
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:listing_id>', methods=['POST'])
def update_cart(listing_id):
    qty = float(request.form['quantity'])
    if qty <= 0:
        return redirect(url_for('remove_from_cart', listing_id=listing_id))
    cart = session.get('cart', {})
    cart[str(listing_id)] = qty
    session['cart'] = cart
    return redirect(url_for('cart'))

# ---------- CHECKOUT & ORDERS ----------
import json as jsonlib

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))
    # Calculate total
    total = 0.0
    items_list = []
    for lid, qty in cart.items():
        listing = Listing.query.get(int(lid))
        if listing:
            subtotal = listing.price_per_kg * qty
            total += subtotal
            items_list.append({
                'title': listing.title,
                'price': listing.price_per_kg,
                'quantity': qty,
                'subtotal': subtotal
            })
    if request.method == 'POST':
        address = request.form['address']
        payment = request.form['payment']
        # Create order
        order = Order(
            user_id=session['user_id'],
            items=jsonlib.dumps(items_list),
            total_amount=total,
            address=address,
            payment_method=payment,
            status='Pending'
        )
        db.session.add(order)
        db.session.commit()
        # Clear cart
        session['cart'] = {}
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_status', order_id=order.id))
    return render_template('checkout.html', items=items_list, total=total)

@app.route('/order/<int:order_id>')
@login_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        flash('Unauthorized', 'danger')
        return redirect(url_for('cart'))
    items = jsonlib.loads(order.items)
    return render_template('order_status.html', order=order, items=items)

@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/tracking')
@login_required
def tracking_dashboard():
    return render_template('tracking.html')

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html')
