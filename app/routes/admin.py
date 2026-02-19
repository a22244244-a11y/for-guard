from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import User, Customer, Submission, Script

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

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


@admin_bp.route('/admin/submission/<int:submission_id>')
@login_required
def admin_submission_detail(submission_id):
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    submission = Submission.query.get_or_404(submission_id)
    return render_template('admin_submission_detail.html', submission=submission)


@admin_bp.route('/admin/submission/<int:submission_id>/resolve', methods=['POST'])
@login_required
def resolve_submission(submission_id):
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    submission = Submission.query.get_or_404(submission_id)
    submission.admin_status = '처리완료'
    db.session.commit()

    flash('처리완료로 변경되었습니다.', 'success')
    return redirect(url_for('admin.admin_submission_detail', submission_id=submission_id))


# === 프리랜서 계정 관리 ===

@admin_bp.route('/admin/freelancers')
@login_required
def manage_freelancers():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    freelancers = User.query.filter_by(role='freelancer').all()
    return render_template('admin_freelancers.html', freelancers=freelancers)


@admin_bp.route('/admin/freelancers/create', methods=['POST'])
@login_required
def create_freelancer():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        flash('아이디와 비밀번호를 모두 입력해주세요.', 'error')
        return redirect(url_for('admin.manage_freelancers'))

    if User.query.filter_by(username=username).first():
        flash('이미 존재하는 아이디입니다.', 'error')
        return redirect(url_for('admin.manage_freelancers'))

    new_user = User(
        username=username,
        password=generate_password_hash(password, method='pbkdf2:sha256'),
        role='freelancer'
    )
    db.session.add(new_user)
    db.session.commit()
    flash(f'프리랜서 계정 "{username}"이 생성되었습니다.', 'success')
    return redirect(url_for('admin.manage_freelancers'))


@admin_bp.route('/admin/freelancers/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_freelancer(user_id):
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    user = User.query.get_or_404(user_id)
    if user.role != 'freelancer':
        flash('프리랜서 계정만 삭제할 수 있습니다.', 'error')
        return redirect(url_for('admin.manage_freelancers'))

    # 배정된 고객 해제
    Customer.query.filter_by(assigned_agent_id=user_id).update({'assigned_agent_id': None})
    db.session.delete(user)
    db.session.commit()
    flash(f'프리랜서 계정 "{user.username}"이 삭제되었습니다.', 'success')
    return redirect(url_for('admin.manage_freelancers'))


# === 스크립트 편집 ===

@admin_bp.route('/admin/script')
@login_required
def edit_script():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    active_script = Script.query.filter_by(is_active=True).first()
    variables = [
        ('[단말기명]', '개통 단말기 모델명'),
        ('[할부원금]', '월 할부금액'),
        ('[할부기간]', '할부 개월수'),
        ('[약정기간]', '약정 개월수'),
        ('[요금제명]', '개통 요금제'),
        ('[요금제기본료]', '요금제 기본료'),
        ('[부가서비스1]', '부가서비스 1'),
        ('[부가서비스2]', '부가서비스 2'),
        ('[요금제유지일수]', '요금제 의무유지 일수'),
        ('[부가서비스유지일수]', '부가서비스 유지 일수'),
        ('[청구기간]', '청구 기간'),
        ('[청구예상금액]', '월 청구 예상금액'),
        ('[변경후청구금액]', '요금제 변경 후 청구금액'),
        ('[기존할부잔여기간]', '기존 할부 잔여기간'),
        ('[기존할부금]', '기존 할부금'),
        ('[위약금]', '위약금 금액'),
        ('[처리방법]', '잔여할부/위약금 처리방법'),
    ]
    return render_template('admin_script_edit.html', script=active_script, variables=variables)


@admin_bp.route('/admin/script/save', methods=['POST'])
@login_required
def save_script():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    content = request.form.get('content', '')
    title = request.form.get('title', '기본 해피콜 스크립트')

    active_script = Script.query.filter_by(is_active=True).first()
    if active_script:
        active_script.content = content
        active_script.title = title
        active_script.updated_at = datetime.utcnow()
    else:
        active_script = Script(title=title, content=content, is_active=True, created_by=current_user.id)
        db.session.add(active_script)

    db.session.commit()
    flash('스크립트가 저장되었습니다.', 'success')
    return redirect(url_for('admin.edit_script'))


# === 고객 관리 (배정/회수) ===

@admin_bp.route('/admin/customers')
@login_required
def manage_customers():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    status_filter = request.args.get('status', 'all')
    query = Customer.query

    if status_filter != 'all':
        query = query.filter(Customer.call_status == status_filter)

    customers = query.order_by(Customer.created_at.desc()).all()
    freelancers = User.query.filter_by(role='freelancer').all()

    status_counts = {
        'all': Customer.query.count(),
        '대기': Customer.query.filter_by(call_status='대기').count(),
        '1차부재': Customer.query.filter_by(call_status='1차부재').count(),
        '2차부재': Customer.query.filter_by(call_status='2차부재').count(),
        '3차부재': Customer.query.filter_by(call_status='3차부재').count(),
        '통화거부': Customer.query.filter_by(call_status='통화거부').count(),
        '해피콜완료': Customer.query.filter_by(call_status='해피콜완료').count(),
    }

    return render_template('admin_customers.html',
                         customers=customers,
                         freelancers=freelancers,
                         status_filter=status_filter,
                         status_counts=status_counts)


@admin_bp.route('/admin/customers/assign', methods=['POST'])
@login_required
def assign_customer():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    customer_id = request.form.get('customer_id', type=int)
    agent_id = request.form.get('agent_id', '').strip()

    customer = Customer.query.get_or_404(customer_id)

    if agent_id:
        customer.assigned_agent_id = int(agent_id)
        agent = User.query.get(int(agent_id))
        flash(f'{customer.name} → {agent.username} 배정 완료', 'success')
    else:
        customer.assigned_agent_id = None
        flash(f'{customer.name} 배정 해제', 'info')

    db.session.commit()
    return redirect(url_for('admin.manage_customers'))


@admin_bp.route('/admin/customers/bulk-assign', methods=['POST'])
@login_required
def bulk_assign_customers():
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    customer_ids = request.form.getlist('customer_ids')
    agent_id = request.form.get('bulk_agent_id', '').strip()

    if not customer_ids:
        flash('고객을 선택해주세요.', 'error')
        return redirect(url_for('admin.manage_customers'))

    for cid in customer_ids:
        customer = Customer.query.get(int(cid))
        if customer:
            customer.assigned_agent_id = int(agent_id) if agent_id else None

    db.session.commit()
    action = '배정' if agent_id else '배정 해제'
    flash(f'{len(customer_ids)}건 {action} 완료', 'success')
    return redirect(url_for('admin.manage_customers'))


@admin_bp.route('/admin/customers/create', methods=['POST'])
@login_required
def create_customer():
    """수동으로 고객 추가 (API 연동 전 테스트용)"""
    if current_user.role != 'admin':
        flash('관리자만 접근 가능합니다.', 'error')
        return redirect(url_for('auth.index'))

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not name or not phone:
        flash('고객명과 연락처를 모두 입력해주세요.', 'error')
        return redirect(url_for('admin.manage_customers'))

    customer = Customer(name=name, phone=phone)
    db.session.add(customer)
    db.session.commit()
    flash(f'고객 "{name}"이 추가되었습니다.', 'success')
    return redirect(url_for('admin.manage_customers'))
