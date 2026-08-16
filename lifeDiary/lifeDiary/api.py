from ninja import NinjaAPI, Swagger
from ninja.security import django_auth

api = NinjaAPI(
    title="LifeDiary API",
    version="1.0.0",
    description="10분 슬롯 기록과 태그 관리를 위한 내부 JSON API",
    auth=django_auth,
    docs=Swagger(),
)
