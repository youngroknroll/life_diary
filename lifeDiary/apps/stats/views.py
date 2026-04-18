from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.core.utils import (
    safe_date_parse,
)
from .logic import get_stats_context
from .feedback import generate_feedback
from itertools import islice


def chunked_iterable(iterable, n):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk:
            break
        yield chunk


# Create your views here.


@login_required
def index(request):
    selected_date = safe_date_parse(request.GET.get("date"))
    context = get_stats_context(request.user, selected_date)
    context["feedback_list"] = generate_feedback(context)
    return render(request, "stats/index.html", context)
