import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///happycall.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '로그인이 필요합니다.'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    document_status = db.Column(db.String(50), default='접수완료')
    assigned_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    submissions = db.relationship('Submission', backref='customer', lazy=True)


class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recording_file = db.Column(db.String(200))
    check_installment = db.Column(db.Boolean, default=True)
    check_penalty = db.Column(db.Boolean, default=True)
    check_rate_plan = db.Column(db.Boolean, default=True)
    check_retention = db.Column(db.Boolean, default=True)
    check_monthly_fee = db.Column(db.Boolean, default=True)
    check_used_phone = db.Column(db.Boolean, default=True)
    final_status = db.Column(db.String(20), default='정상')
    admin_status = db.Column(db.String(20), default='대기중')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    agent = db.relationship('User', backref='submissions')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_mock_customers(agent_id):
    existing = Customer.query.filter_by(assigned_agent_id=agent_id).first()
    if existing:
        return
    
    mock_data = [
        {'name': '김철수', 'phone': '010-1234-5678', 'document_status': '접수완료'},
        {'name': '이영희', 'phone': '010-2345-6789', 'document_status': '서류검토중'},
        {'name': '박민수', 'phone': '010-3456-7890', 'document_status': '접수완료'},
        {'name': '정수진', 'phone': '010-4567-8901', 'document_status': '서류검토중'},
        {'name': '최동훈', 'phone': '010-5678-9012', 'document_status': '접수완료'},
    ]
    
    for data in mock_data:
        customer = Customer(
            name=data['name'],
            phone=data['phone'],
            document_status=data['document_status'],
            assigned_agent_id=agent_id
        )
        db.session.add(customer)
    db.session.commit()


def init_db():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='1').first():
            admin = User(
                username='1',
                password=generate_password_hash('1'),
                role='admin'
            )
            db.session.add(admin)
        
        if not User.query.filter_by(username='2').first():
            freelancer = User(
                username='2',
                password=generate_password_hash('2'),
                role='freelancer'
            )
            db.session.add(freelancer)
        
        db.session.commit()


@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('freelancer_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('로그인 성공!', 'success')
            return redirect(url_for('index'))
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃 되었습니다.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def freelancer_dashboard():
    if current_user.role != 'freelancer':
        return redirect(url_for('admin_dashboard'))
    
    generate_mock_customers(current_user.id)
    
    customers = Customer.query.filter_by(assigned_agent_id=current_user.id).all()
    
    customer_status = {}
    for customer in customers:
        submission = Submission.query.filter_by(customer_id=customer.id).first()
        customer_status[customer.id] = '완료' if submission else '대기'
    
    return render_template('freelancer_dashboard.html', customers=customers, customer_status=customer_status)


@app.route('/customer/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    if current_user.role != 'freelancer':
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('index'))
    
    customer = Customer.query.get_or_404(customer_id)
    
    if customer.assigned_agent_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('freelancer_dashboard'))
    
    existing_submission = Submission.query.filter_by(customer_id=customer_id).first()
    
    return render_template('customer_detail.html', customer=customer, submission=existing_submission)


@app.route('/customer/<int:customer_id>/submit', methods=['POST'])
@login_required
def submit_checklist(customer_id):
    if current_user.role != 'freelancer':
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('index'))
    
    customer = Customer.query.get_or_404(customer_id)
    
    if customer.assigned_agent_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('freelancer_dashboard'))
    
    existing = Submission.query.filter_by(customer_id=customer_id).first()
    if existing:
        flash('이미 제출된 건입니다.', 'warning')
        return redirect(url_for('customer_detail', customer_id=customer_id))
    
    recording_file = None
    if 'recording' in request.files:
        file = request.files['recording']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            recording_file = filename
    
    check_installment = request.form.get('check_installment') == 'normal'
    check_penalty = request.form.get('check_penalty') == 'normal'
    check_rate_plan = request.form.get('check_rate_plan') == 'normal'
    check_retention = request.form.get('check_retention') == 'normal'
    check_monthly_fee = request.form.get('check_monthly_fee') == 'normal'
    check_used_phone = request.form.get('check_used_phone') == 'normal'
    
    all_normal = all([
        check_installment, check_penalty, check_rate_plan,
        check_retention, check_monthly_fee, check_used_phone
    ])
    final_status = '정상' if all_normal else '비정상'
    
    submission = Submission(
        customer_id=customer_id,
        agent_id=current_user.id,
        recording_file=recording_file,
        check_installment=check_installment,
        check_penalty=check_penalty,
        check_rate_plan=check_rate_plan,
        check_retention=check_retention,
        check_monthly_fee=check_monthly_fee,
        check_used_phone=check_used_phone,
        final_status=final_status,
        admin_status='대기중'
    )
    
    db.session.add(submission)
    db.session.commit()
    
    flash(f'체크리스트가 제출되었습니다. 결과: {final_status}', 'success')
    return redirect(url_for('freelancer_dashboard'))


@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('index'))
    
    filter_type = request.args.get('filter', 'all')
    
    query = Submission.query.join(Customer)
    
    if filter_type == 'abnormal':
        query = query.filter(Submission.final_status == '비정상')
    elif filter_type == 'pending':
        query = query.filter(Submission.admin_status == '대기중')
    elif filter_type == 'resolved':
        query = query.filter(Submission.admin_status == '처리완료')
    
    submissions = query.order_by(Submission.created_at.desc()).all()
    
    stats = {
        'total': Submission.query.count(),
        'normal': Submission.query.filter_by(final_status='정상').count(),
        'abnormal': Submission.query.filter_by(final_status='비정상').count(),
        'pending': Submission.query.filter_by(admin_status='대기중').count(),
        'resolved': Submission.query.filter_by(admin_status='처리완료').count()
    }
    
    return render_template('admin_dashboard.html', submissions=submissions, stats=stats, filter_type=filter_type)


@app.route('/admin/submission/<int:submission_id>')
@login_required
def admin_submission_detail(submission_id):
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('index'))
    
    submission = Submission.query.get_or_404(submission_id)
    return render_template('admin_submission_detail.html', submission=submission)


@app.route('/admin/submission/<int:submission_id>/resolve', methods=['POST'])
@login_required
def resolve_submission(submission_id):
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('index'))
    
    submission = Submission.query.get_or_404(submission_id)
    submission.admin_status = '처리완료'
    db.session.commit()
    
    flash('처리완료로 변경되었습니다.', 'success')
    return redirect(url_for('admin_submission_detail', submission_id=submission_id))


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
