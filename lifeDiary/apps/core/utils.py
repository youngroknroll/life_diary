"""
=================================================================================
공통 유틸리티 Python 모듈
- 여러 앱에서 공통으로 사용되는 헬퍼 함수들과 상수들을 포함합니다.
=================================================================================
"""

import json
from datetime import datetime, date, timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse

# 공통 상수
UNCLASSIFIED_TAG_NAME = "미분류"
UNCLASSIFIED_TAG_COLOR = "#808080"
SLEEP_TAG_NAME = "수면"

# 시간 관련 상수
SLOTS_PER_HOUR = 6  # 10분 단위
TOTAL_SLOTS_PER_DAY = 144  # 24시간 * 6
MINUTES_PER_SLOT = 10
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7


def serialize_for_js(data):
    """
    Django 객체를 JavaScript에서 사용할 수 있는 JSON 문자열로 직렬화

    Args:
        data: 직렬화할 데이터 (dict, list, 또는 기타 JSON 호환 타입)

    Returns:
        str: JSON 문자열
    """
    return json.dumps(data, cls=DjangoJSONEncoder)


def safe_date_parse(date_str, default=None):
    """
    안전한 날짜 파싱 함수

    Args:
        date_str (str): 파싱할 날짜 문자열 (YYYY-MM-DD 형식)
        default: 파싱 실패 시 반환할 기본값 (None이면 오늘 날짜)

    Returns:
        date: 파싱된 날짜 객체
    """
    if not date_str:
        return default or date.today()

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return default or date.today()


def calculate_time_statistics(blocks_count):
    """
    시간 블록 개수를 기반으로 시간 통계 계산

    Args:
        blocks_count (int): 시간 블록 개수

    Returns:
        dict: 시간 통계 정보
    """
    total_minutes = blocks_count * MINUTES_PER_SLOT
    hours = total_minutes // MINUTES_PER_HOUR
    remaining_minutes = total_minutes % MINUTES_PER_HOUR

    return {
        "total_minutes": total_minutes,
        "hours": hours,
        "remaining_minutes": remaining_minutes,
        "total_hours_float": round(total_minutes / MINUTES_PER_HOUR, 1),
        "fill_percentage": round((blocks_count / TOTAL_SLOTS_PER_DAY) * 100, 1),
    }


def success_response(message, data=None, status=200):
    """
    성공 응답을 위한 표준 JsonResponse 생성

    Args:
        message (str): 성공 메시지
        data (dict, optional): 추가 데이터
        status (int): HTTP 상태 코드

    Returns:
        JsonResponse: 표준화된 성공 응답
    """
    response_data = {"success": True, "message": message}

    if data:
        response_data.update(data)

    return JsonResponse(response_data, status=status)


def error_response(message, error_code=None, status=400):
    """
    오류 응답을 위한 표준 JsonResponse 생성

    Args:
        message (str): 오류 메시지
        error_code (str, optional): 오류 코드
        status (int): HTTP 상태 코드

    Returns:
        JsonResponse: 표준화된 오류 응답
    """
    response_data = {"success": False, "message": message}

    if error_code:
        response_data["error"] = error_code

    return JsonResponse(response_data, status=status)


def get_slot_from_time(hour, minute):
    """
    시간(시, 분)을 슬롯 인덱스로 변환

    Args:
        hour (int): 시 (0-23)
        minute (int): 분 (0-59, 10분 단위로 반올림됨)

    Returns:
        int: 슬롯 인덱스 (0-143)
    """
    # 10분 단위로 반올림
    slot_minute = (minute // MINUTES_PER_SLOT) * MINUTES_PER_SLOT
    return hour * SLOTS_PER_HOUR + (slot_minute // MINUTES_PER_SLOT)


def get_time_from_slot(slot_index):
    """
    슬롯 인덱스를 시간(시, 분)으로 변환

    Args:
        slot_index (int): 슬롯 인덱스 (0-143)

    Returns:
        tuple: (시, 분) 튜플
    """
    hour = slot_index // SLOTS_PER_HOUR
    minute = (slot_index % SLOTS_PER_HOUR) * MINUTES_PER_SLOT
    return hour, minute


def format_time_display(hours, minutes):
    """
    시간을 사용자 친화적 형식으로 포맷팅

    Args:
        hours (int): 시간
        minutes (int): 분

    Returns:
        str: 포맷팅된 시간 문자열
    """
    if hours > 0 and minutes > 0:
        return f"{hours}시간 {minutes}분"
    elif hours > 0:
        return f"{hours}시간"
    elif minutes > 0:
        return f"{minutes}분"
    else:
        return "0분"



def get_week_date_range(target_date):
    """
    주어진 날짜가 포함된 주의 시작일과 종료일을 반환 (월요일 시작)

    Args:
        target_date (date): 기준 날짜

    Returns:
        tuple: (시작일, 종료일) 튜플
    """
    # 월요일을 주의 시작으로 설정 (weekday: 월=0, 일=6)
    days_since_monday = target_date.weekday()
    start_date = target_date - timedelta(days=days_since_monday)
    end_date = start_date + timedelta(days=6)

    return start_date, end_date


def get_month_date_range(target_date):
    """
    주어진 날짜가 포함된 월의 시작일과 종료일을 반환

    Args:
        target_date (date): 기준 날짜

    Returns:
        tuple: (시작일, 종료일) 튜플
    """
    from calendar import monthrange

    start_date = target_date.replace(day=1)
    last_day = monthrange(target_date.year, target_date.month)[1]
    end_date = target_date.replace(day=last_day)

    return start_date, end_date
