import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Customer, Submission, Script
from app.services import allowed_file

freelancer_bp = Blueprint('freelancer', __name__)


@freelancer_bp.route('/dashboard')
@login_required
def freelancer_dashboard():
    if current_user.role != 'freelancer':
        return redirect(url_for('admin.admin_dashboard'))

    customers = Customer.query.filter_by(assigned_agent_id=current_user.id).all()
    return render_template('freelancer_dashboard.html', customers=customers)


@freelancer_bp.route('/customer/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    if current_user.role != 'freelancer':
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    customer = Customer.query.get_or_404(customer_id)
    if customer.assigned_agent_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('freelancer.freelancer_dashboard'))

    existing_submission = Submission.query.filter_by(customer_id=customer_id).first()
    active_script = Script.query.filter_by(is_active=True).first()
    return render_template('customer_detail.html', customer=customer, submission=existing_submission, script=active_script)


@freelancer_bp.route('/customer/<int:customer_id>/status', methods=['POST'])
@login_required
def update_call_status(customer_id):
    if current_user.role != 'freelancer':
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    customer = Customer.query.get_or_404(customer_id)
    if customer.assigned_agent_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('freelancer.freelancer_dashboard'))

    new_status = request.form.get('call_status')
    valid_statuses = ['대기', '1차부재', '2차부재', '3차부재', '통화거부']

    if new_status not in valid_statuses:
        flash('유효하지 않은 상태입니다.', 'error')
        return redirect(url_for('freelancer.customer_detail', customer_id=customer_id))

    customer.call_status = new_status
    db.session.commit()
    flash(f'상태가 "{new_status}"로 변경되었습니다.', 'success')
    return redirect(url_for('freelancer.customer_detail', customer_id=customer_id))


@freelancer_bp.route('/customer/<int:customer_id>/submit', methods=['POST'])
@login_required
def submit_checklist(customer_id):
    if current_user.role != 'freelancer':
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    customer = Customer.query.get_or_404(customer_id)
    if customer.assigned_agent_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('freelancer.freelancer_dashboard'))

    existing = Submission.query.filter_by(customer_id=customer_id).first()
    if existing:
        flash('이미 제출된 건입니다.', 'warning')
        return redirect(url_for('freelancer.customer_detail', customer_id=customer_id))

    recording_file = None
    if 'recording' in request.files:
        file = request.files['recording']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            recording_file = filename

    if not recording_file:
        flash('녹취 파일을 업로드해주세요.', 'error')
        return redirect(url_for('freelancer.customer_detail', customer_id=customer_id))

    check_installment = request.form.get('check_installment') == 'normal'
    check_penalty = request.form.get('check_penalty') == 'normal'
    check_rate_plan = request.form.get('check_rate_plan') == 'normal'
    check_retention = request.form.get('check_retention') == 'normal'
    check_monthly_fee = request.form.get('check_monthly_fee') == 'normal'
    check_used_phone = request.form.get('check_used_phone') == 'normal'
    check_store_complaint = request.form.get('check_store_complaint') == 'normal'
    memo_check_installment = request.form.get('memo_check_installment', '')
    memo_check_penalty = request.form.get('memo_check_penalty', '')
    memo_check_rate_plan = request.form.get('memo_check_rate_plan', '')
    memo_check_retention = request.form.get('memo_check_retention', '')
    memo_check_monthly_fee = request.form.get('memo_check_monthly_fee', '')
    memo_check_used_phone = request.form.get('memo_check_used_phone', '')
    store_complaint_memo = request.form.get('store_complaint_memo', '')
    agent_opinion = request.form.get('agent_opinion', '')
    raw_customer_data = request.form.get('raw_customer_data', '')

    all_normal = all([
        check_installment, check_penalty, check_rate_plan,
        check_retention, check_monthly_fee, check_used_phone,
        check_store_complaint
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
        check_store_complaint=check_store_complaint,
        memo_check_installment=memo_check_installment,
        memo_check_penalty=memo_check_penalty,
        memo_check_rate_plan=memo_check_rate_plan,
        memo_check_retention=memo_check_retention,
        memo_check_monthly_fee=memo_check_monthly_fee,
        memo_check_used_phone=memo_check_used_phone,
        store_complaint_memo=store_complaint_memo,
        agent_opinion=agent_opinion,
        raw_customer_data=raw_customer_data,
        final_status=final_status,
        admin_status='대기중'
    )

    db.session.add(submission)
    customer.call_status = '해피콜완료'
    db.session.commit()

    flash(f'체크리스트가 제출되었습니다. 결과: {final_status}', 'success')
    return redirect(url_for('freelancer.freelancer_dashboard'))
