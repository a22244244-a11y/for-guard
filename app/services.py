from flask import current_app
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import User, Script


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


DEFAULT_SCRIPT_HTML = """<!-- 인사말 -->
<div class="bg-brand-50 rounded-lg px-4 py-3 border border-brand-100">
    <p class="font-semibold text-brand-600 text-xs uppercase tracking-wider mb-2">개통 해피콜</p>
    <p class="font-medium text-brand-700">"안녕하세요 고객님, 휴대폰 가입을 도와드린 LG유플러스 포피플 대리점입니다. 개통 이후 계약 내용이 정확하게 안내되었는지 확인드리기 위해 연락드렸는데 시간은 2~3분 정도 소요됩니다. 시간 괜찮으실까요?"</p>
</div>

<!-- YES/NO 분기 -->
<div class="flex gap-2 text-xs">
    <span class="inline-flex items-center gap-1 bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full font-semibold">
        <i class="fas fa-check text-[10px]"></i> YES
    </span>
    <span class="text-gray-500 leading-relaxed">아래 스크립트로 진행</span>
</div>
<div class="flex gap-2 text-xs">
    <span class="inline-flex items-center gap-1 bg-red-100 text-red-700 px-2.5 py-1 rounded-full font-semibold">
        <i class="fas fa-xmark text-[10px]"></i> NO
    </span>
    <span class="text-gray-500 leading-relaxed">"통화가능 하신 시간이 있다면 편하신 시간에 연락 드리겠습니다"</span>
</div>

<div class="border-t border-blue-100"></div>

<!-- STEP 1: 단말기/약정 -->
<div class="bg-white rounded-xl p-4 border border-surface-200">
    <div class="flex items-center gap-2 mb-3">
        <span class="w-6 h-6 rounded-md bg-brand-500 text-white text-xs font-bold flex items-center justify-center">1</span>
        <span class="font-semibold text-gray-800 text-sm">단말기 / 약정 확인</span>
    </div>
    <div class="space-y-2 text-gray-600 text-[13px] leading-relaxed">
        <p>"구입하신 단말기는 [단말기명]로 할부 [할부원금], [할부기간]로 개통되었습니다. 개통 당시 설명을 들으셨나요?"</p>
        <p>"약정은 [약정기간]로, 약정 기간 내 해지나 번호이동, 기기변경 시 위약금이 발생할 수 있다는 점도 안내 받으셨을까요?"</p>
    </div>
    <div class="mt-3 pt-3 border-t border-surface-100 flex flex-col gap-1.5 text-xs">
        <div class="flex gap-2">
            <span class="inline-flex items-center gap-1 bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-semibold flex-shrink-0">
                <i class="fas fa-check text-[9px]"></i> YES
            </span>
            <span class="text-gray-500">아래 스크립트로 진행</span>
        </div>
        <div class="flex gap-2">
            <span class="inline-flex items-center gap-1 bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-semibold flex-shrink-0">
                <i class="fas fa-xmark text-[9px]"></i> NO
            </span>
            <span class="text-gray-500">(이상 응답건 메모) "정확한 내용 재안내를 위해 담당자에게 전달하겠습니다"</span>
        </div>
    </div>
</div>

<!-- STEP 2: 요금제/부가서비스 -->
<div class="bg-white rounded-xl p-4 border border-surface-200">
    <div class="flex items-center gap-2 mb-3">
        <span class="w-6 h-6 rounded-md bg-brand-500 text-white text-xs font-bold flex items-center justify-center">2</span>
        <span class="font-semibold text-gray-800 text-sm">요금제 / 부가서비스 확인</span>
    </div>
    <div class="space-y-2 text-gray-600 text-[13px] leading-relaxed">
        <p>"개통당시 가입하신 요금제는 [요금제명], 기본료는 [요금제기본료]입니다. 부가서비스는 [부가서비스1]와 [부가서비스2]가 등록되어있는데 정확히 안내 받으셨을까요?"</p>
        <p>"요금제는 [요금제유지일수] 유지 후 변경 가능하며, 부가서비스는 [부가서비스유지일수] 후 언제든지 삭제 가능합니다. 의무 유지기간이 있다는 점에 대해서도 안내받으셨을까요?"</p>
        <p>"매월 청구되는 요금은 [청구기간]동안 [청구예상금액], 이후 요금제 변경 시 [변경후청구금액] 청구되며 단말기 할부금이 포함된 요금으로 안내 받으신 내용과 다른 부분 있는지 확인 부탁드립니다."</p>
        <p>"요금제 변경, 부가서비스 삭제는 자동으로 변경/삭제 되지 않으니 해당기간 이후 고객님께서 직접 내방 또는 전화주시면 변경 가능합니다."</p>
    </div>
    <div class="mt-3 pt-3 border-t border-surface-100 flex flex-col gap-1.5 text-xs">
        <div class="flex gap-2">
            <span class="inline-flex items-center gap-1 bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-semibold flex-shrink-0">
                <i class="fas fa-check text-[9px]"></i> YES
            </span>
            <span class="text-gray-500">아래 스크립트로 진행</span>
        </div>
        <div class="flex gap-2">
            <span class="inline-flex items-center gap-1 bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-semibold flex-shrink-0">
                <i class="fas fa-xmark text-[9px]"></i> NO
            </span>
            <span class="text-gray-500">(이상 응답건 메모) "정확한 내용 재안내를 위해 담당자에게 전달하겠습니다"</span>
        </div>
    </div>
</div>

<!-- STEP 3: 중고폰/추가확인 -->
<div class="bg-white rounded-xl p-4 border border-surface-200">
    <div class="flex items-center gap-2 mb-3">
        <span class="w-6 h-6 rounded-md bg-brand-500 text-white text-xs font-bold flex items-center justify-center">3</span>
        <span class="font-semibold text-gray-800 text-sm">중고폰 반납 / 추가 확인</span>
    </div>
    <div class="space-y-2 text-gray-600 text-[13px] leading-relaxed">
        <p>"중고폰 반납이 진행된 경우, 중고폰 반납 여부와 반납 후 처리 방식에 대해 안내를 받으셨는지 확인드리겠습니다." <span class="text-gray-400 text-xs">(중고폰 반납이 없는 경우 해당 없다고 말씀 주셔도 됩니다.)</span></p>
        <p>"개통 당시 기존 단말기 할부금은 [기존할부잔여기간], [기존할부금] 남아있었고 위약금도 [위약금] 발생되는 부분 안내 받으셨나요? 잔여할부 or 위약금은 [처리방법]로 정확히 안내 받으셨는지 확인 부탁드립니다."</p>
        <p>"추가로 고객님께 약속 드린 사항에 대해 이행되지 않은 부분이 있을까요?"</p>
    </div>
    <div class="mt-3 pt-3 border-t border-surface-100 flex flex-col gap-1.5 text-xs">
        <div class="flex gap-2">
            <span class="inline-flex items-center gap-1 bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-semibold flex-shrink-0">
                <i class="fas fa-check text-[9px]"></i> YES
            </span>
            <span class="text-gray-500">아래 마무리 멘트로 진행</span>
        </div>
        <div class="flex gap-2">
            <span class="inline-flex items-center gap-1 bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-semibold flex-shrink-0">
                <i class="fas fa-xmark text-[9px]"></i> NO
            </span>
            <span class="text-gray-500">(이상 응답건 메모) "정확한 내용 재안내를 위해 담당자에게 전달하겠습니다"</span>
        </div>
    </div>
</div>

<div class="border-t border-blue-100"></div>

<!-- 마무리 -->
<div class="bg-brand-50 rounded-lg px-4 py-3 border border-brand-100 space-y-2">
    <p class="font-semibold text-brand-600 text-xs uppercase tracking-wider">마무리</p>
    <p class="font-medium text-brand-700 text-[13px] leading-relaxed">"지금까지 확인드린 내용 중에서 안내받은 내용과 다르거나 확인이 필요한 건으로 담당자에게 전달하여 빠르게 재확인 할 수 있도록 하겠습니다. 추가로 궁금하신 점이나 불편하셨던 사항이 있을까요?"</p>
    <p class="font-medium text-brand-700 text-[13px] leading-relaxed">"오늘 확인된 내용은 기록하여 관리될 예정이며, 추가 안내가 필요한 경우 개통 도와드린 담당자가 다시 연락드리겠습니다. 감사합니다."</p>
</div>"""


def init_db():
    db.create_all()

    admin_user = current_app.config['TEST_ADMIN_USERNAME']
    admin_pass = current_app.config['TEST_ADMIN_PASSWORD']
    freelancer_user = current_app.config['TEST_FREELANCER_USERNAME']
    freelancer_pass = current_app.config['TEST_FREELANCER_PASSWORD']

    if not User.query.filter_by(username=admin_user).first():
        admin = User(
            username=admin_user,
            password=generate_password_hash(admin_pass, method='pbkdf2:sha256'),
            role='admin'
        )
        db.session.add(admin)

    if not User.query.filter_by(username=freelancer_user).first():
        freelancer = User(
            username=freelancer_user,
            password=generate_password_hash(freelancer_pass, method='pbkdf2:sha256'),
            role='freelancer'
        )
        db.session.add(freelancer)

    if not Script.query.first():
        default_script = Script(
            title='기본 해피콜 스크립트',
            content=DEFAULT_SCRIPT_HTML,
            is_active=True,
            created_by=1
        )
        db.session.add(default_script)

    db.session.commit()
