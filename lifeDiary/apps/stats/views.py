from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.core.utils import safe_date_parse
from .life_feedback import generate_feedback
from .use_cases import GetStatsContextUseCase

_get_stats_context = GetStatsContextUseCase()


@login_required
def index(request):
    selected_date = safe_date_parse(request.GET.get("date"))
    context = _get_stats_context.execute(request.user, selected_date)
    context["feedback_list"] = generate_feedback(context)
    return render(request, "stats/index.html", context)
