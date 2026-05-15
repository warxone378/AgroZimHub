from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Listing, Order, ForumPost, ForumReply
from config import SECRET_KEY, PROVINCES, SOIL_TYPES, SEED_TYPES
from services.ai_engine import AIEngine
from services.weather import WeatherService
from services.fintech import FintechLogic
from functools import wraps
from datetime import datetime
import json, os, time, random

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/data/com.termux/files/home/agrozim.db'
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

# ---------- AUTH ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'Farmer')
        phone = request.form.get('phone', '')
        province = request.form.get('province', 'Harare')
        if not username or not password:
            flash('Username and password required.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, role=role, phone_number=phone, location_province=province)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', provinces=PROVINCES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ---------- PROFILE ----------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.phone_number = request.form.get('phone', user.phone_number)
        user.location_province = request.form.get('province', user.location_province)
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                filename = secure_filename(f"user_{user.id}_{time.time()}.jpg")
                os.makedirs('static/uploads', exist_ok=True)
                file.save(os.path.join('static/uploads', filename))
                user.avatar = filename
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user, provinces=PROVINCES)

# ---------- FORGOT PASSWORD ----------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username', '')
        user = User.query.filter_by(username=username).first()
        if user:
            reset_link = f"http://localhost:5000/reset_password/{user.id}"
            print(f"🔐 PASSWORD RESET LINK: {reset_link}")
            flash('Reset link printed in console.', 'info')
        else:
            flash('No account with that username.', 'danger')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            user.set_password(password)
            db.session.commit()
            flash('Password reset successful.', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html')

# ---------- AI PREDICTOR ----------
@app.route('/predictor', methods=['GET', 'POST'])
@login_required
def predictor():
    recommendation = None
    if request.method == 'POST':
        province = request.form.get('province', 'Harare')
        seed_type = request.form.get('seed_type', 'Hybrid Maize')
        hectares = float(request.form.get('hectares', 1))
        soil_type = request.form.get('soil_type', 'Loam')
        soil_ph = float(request.form.get('soil_ph', 6.5))
        recommendation = AIEngine.predict_planting_strategy(province, seed_type, hectares, soil_type, soil_ph)
    return render_template('predictor.html', provinces=PROVINCES, seed_types=SEED_TYPES, soil_types=SOIL_TYPES, recommendation=recommendation)

# ---------- MARKETPLACE ----------
@app.route('/marketplace')
def marketplace():
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    query = Listing.query
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

@app.route('/listing/<int:id>/delete', methods=['POST'])
@login_required
def delete_listing(id):
    listing = Listing.query.get_or_404(id)
    if listing.seller_id != session['user_id']:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('marketplace'))
    db.session.delete(listing)
    db.session.commit()
    flash('Listing deleted.', 'success')
    return redirect(url_for('marketplace'))

# ---------- CART & CHECKOUT ----------
@app.route('/add_to_cart/<int:listing_id>', methods=['POST'])
def add_to_cart(listing_id):
    qty = float(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[str(listing_id)] = cart.get(str(listing_id), 0) + qty
    session['cart'] = cart
    flash('Added to cart.', 'success')
    return redirect(request.referrer or url_for('marketplace'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    items = []
    total = 0.0
    for lid, qty in cart_items.items():
        listing = Listing.query.get(int(lid))
        if listing:
            subtotal = listing.price_per_kg * qty
            items.append({'listing': listing, 'quantity': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template('cart.html', items=items, total=total)

@app.route('/remove_from_cart/<int:listing_id>')
def remove_from_cart(listing_id):
    cart = session.get('cart', {})
    cart.pop(str(listing_id), None)
    session['cart'] = cart
    flash('Removed.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Cart empty.', 'warning')
        return redirect(url_for('cart'))
    items_list = []
    total = 0.0
    for lid, qty in cart.items():
        listing = Listing.query.get(int(lid))
        if listing:
            subtotal = listing.price_per_kg * qty
            total += subtotal
            items_list.append({'title': listing.title, 'price': listing.price_per_kg, 'quantity': qty, 'subtotal': subtotal})
    if request.method == 'POST':
        order = Order(
            user_id=session['user_id'],
            items=json.dumps(items_list),
            total_amount=total,
            address=request.form['address'],
            payment_method=request.form['payment'],
            status='Pending'
        )
        db.session.add(order)
        db.session.commit()
        session['cart'] = {}
        flash('Order placed!', 'success')
        return redirect(url_for('order_status', order_id=order.id))
    return render_template('checkout.html', items=items_list, total=total)

@app.route('/order/<int:order_id>')
@login_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        flash('Unauthorized', 'danger')
        return redirect(url_for('cart'))
    items = json.loads(order.items)
    return render_template('order_status.html', order=order, items=items)

@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

# ---------- WEATHER ----------
@app.route('/weather_warnings')
@login_required
def weather_warnings():
    user = User.query.get(session['user_id'])
    city = user.location_province or 'Harare'
    weather = WeatherService.get_weather_data(f"{city},ZW")
    analysis = WeatherService.analyze_weather_risks(weather)
    return render_template('weather_warnings.html', weather=weather, analysis=analysis)

# ---------- SILO DASHBOARD ----------
@app.route('/silo_dashboard')
@login_required
def silo_dashboard():
    silo = {
        'moisture': round(random.uniform(8, 14.5), 1),
        'temperature': round(random.uniform(18, 32), 1),
        'fill_level': random.randint(20, 95),
        'grain_quality': random.choice(['Excellent', 'Good', 'Fair', 'Warning'])
    }
    return render_template('silo_dashboard.html', silo=silo)

# ---------- INSURANCE ----------
@app.route('/buy_insurance', methods=['GET', 'POST'])
@login_required
def buy_insurance():
    if request.method == 'POST':
        trigger = request.form.get('trigger_type')
        threshold = float(request.form.get('threshold', 0))
        payout = float(request.form.get('payout', 0))
        premium = payout * 0.05
        flash(f'Insurance purchased! Premium: ${premium:.2f}', 'success')
        return redirect(url_for('buy_insurance'))
    return render_template('buy_insurance.html')

# ---------- ANTI-COUNTERFEIT ----------
@app.route('/verify_batch', methods=['GET', 'POST'])
@login_required
def verify_batch():
    result = None
    if request.method == 'POST':
        batch_id = request.form.get('batch_id', '')
        if batch_id.startswith('AGRO'):
            result = {'status': 'genuine', 'product': 'Hybrid Maize', 'manufacturer': 'SeedCo'}
        else:
            result = {'status': 'fake', 'message': 'Batch not found'}
    return render_template('verify_batch.html', result=result)

# ---------- FORUM ----------
@app.route('/forum')
def forum():
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    return render_template('forum.html', posts=posts)

@app.route('/forum/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        post = ForumPost(title=title, content=content, author_id=session['user_id'])
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('forum'))
    return render_template('post_form.html')

@app.route('/forum/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if request.method == 'POST' and session.get('user_id'):
        content = request.form.get('content', '')
        reply = ForumReply(content=content, post_id=post.id, author_id=session['user_id'])
        db.session.add(reply)
        db.session.commit()
        flash('Reply added.', 'success')
        return redirect(url_for('view_post', post_id=post.id))
    replies = ForumReply.query.filter_by(post_id=post.id).order_by(ForumReply.created_at).all()
    return render_template('post_detail.html', post=post, replies=replies)

# ---------- ADDITIONAL ROUTES FOR BASE.HTML ----------
@app.route('/agronomists')
def agronomists():
    agros = User.query.filter_by(role='Agronomist').all()
    return render_template('agronomists.html', agronomists=agros)

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/disease')
@login_required
def disease():
    return render_template('disease.html')

@app.route('/sms')
@login_required
def sms():
    return render_template('sms.html')

@app.route('/prices')
@login_required
def prices():
    return render_template('prices.html')

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html')

@app.route('/tracking')
@login_required
def tracking():
    return render_template('tracking.html')

# ---------- PLACEHOLDERS FOR MISSING PAGES ----------
@app.route('/insurance_dashboard')
@login_required
def insurance_dashboard():
    return redirect(url_for('buy_insurance'))

@app.route('/disease_detector')
@login_required
def disease_detector():
    return redirect(url_for('disease'))

@app.route('/input_matcher')
@login_required
def input_matcher():
    return redirect(url_for('verify_batch'))

@app.route('/ledger')
@login_required
def ledger():
    return redirect(url_for('verify_batch'))

@app.route('/market_prices')
@login_required
def market_prices():
    return redirect(url_for('prices'))

@app.route('/real_prices')
@login_required
def real_prices():
    return redirect(url_for('prices'))

@app.route('/forecast')
@login_required
def forecast():
    return redirect(url_for('weather_warnings'))

@app.route('/agrovets')
@login_required
def agrovets():
    return render_template('agrovets.html')

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/wallet')
@login_required
def wallet():
    return render_template('wallet.html')

@app.route('/chat_list')
@login_required
def chat_list():
    return render_template('chat_list.html')

@app.route('/chat_room/<int:receiver_id>')
@login_required
def chat_room(receiver_id):
    return render_template('chat_room.html', receiver_id=receiver_id)

@app.route('/add_money', methods=['POST'])
@login_required
def add_money():
    flash('Wallet feature coming soon.', 'info')
    return redirect(url_for('wallet'))

@app.route('/add_reminder', methods=['POST'])
@login_required
def add_reminder():
    flash('Calendar reminders coming soon.', 'info')
    return redirect(url_for('calendar'))

@app.template_filter('usd_to_zig')
def usd_to_zig_filter(amount):
    return FintechLogic.usd_to_zig(amount)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
