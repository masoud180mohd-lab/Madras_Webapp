from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models import RekodiUkaguzi
from ..permissions import CAP_MANAGE_STUDENTS, CAP_FEES, ruhusa_capability
from .helpers import paginate_items


@login_required(login_url="ingia")
@ruhusa_capability(CAP_MANAGE_STUDENTS, CAP_FEES)
def orodha_ukaguzi(request):
    """Recent who-recorded-what for mahudhurio and malipo."""
    kitendo = request.GET.get("kitendo", "")
    qs = RekodiUkaguzi.objects.select_related(
        "mtumiaji", "darasa", "somo", "mwanafunzi", "malipo"
    )
    if kitendo in {
        RekodiUkaguzi.KITENDO_MAHUDHURIO_KAWAIDA,
        RekodiUkaguzi.KITENDO_MAHUDHURIO_HIFDHU,
        RekodiUkaguzi.KITENDO_MALIPO,
    }:
        qs = qs.filter(kitendo=kitendo)

    page_obj, pagination_query = paginate_items(request, qs, per_page=30)
    return render(
        request,
        "usimamizi/orodha_ukaguzi.html",
        {
            "page_obj": page_obj,
            "rekodi": page_obj,
            "pagination_query": pagination_query,
            "kitendo_filter": kitendo,
            "kitendo_choices": RekodiUkaguzi.KITENDO_CHOICES,
        },
    )
