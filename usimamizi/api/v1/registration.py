"""Staff registration create endpoints for the mobile Usajili hub."""

from __future__ import annotations

from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from usimamizi.api.permissions import HasCapability
from usimamizi.forms import DarasaForm, MwalimuCreateForm, MwanafunziForm, SomoForm
from usimamizi.models import Darasa, Mwalimu, Mwanafunzi, Somo
from usimamizi.permissions import CAP_MANAGE_STUDENTS


def _form_data(request):
    data = request.data
    if hasattr(data, "copy") and not isinstance(data, dict):
        payload = data.copy()
    else:
        payload = dict(data)
    return {
        key: "" if value is None else value
        for key, value in payload.items()
        if key != "picha"
    }


def _form_errors(form):
    return {field: [str(err) for err in errors] for field, errors in form.errors.items()}


class UsajiliChaguziView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MANAGE_STUDENTS

    def get(self, request):
        madarasa = [
            {"id": row.id, "jina": row.jina}
            for row in Darasa.objects.order_by("jina")
        ]
        walimu = [
            {
                "id": row.id,
                "jina": row.user.get_full_name() or row.user.username,
            }
            for row in Mwalimu.objects.select_related("user").order_by(
                "user__first_name", "user__username"
            )
        ]
        masomo = [
            {"id": row.id, "jina": row.jina, "ni_la_hifdhu": row.ni_la_hifdhu}
            for row in Somo.objects.order_by("jina")
        ]
        return Response(
            {
                "madarasa": madarasa,
                "walimu": walimu,
                "masomo": masomo,
                "jinsia": [
                    {"value": value, "label": label}
                    for value, label in Mwanafunzi._meta.get_field("jinsia").choices
                ],
                "uhusiano": [
                    {"value": value, "label": label}
                    for value, label in Mwanafunzi.UHUSIANO_MLEZI_CHOICES
                ],
                "cheo": [
                    {"value": value, "label": label}
                    for value, label in Mwalimu._meta.get_field("cheo").choices
                ],
            }
        )


class UsajiliMwanafunziCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MANAGE_STUDENTS

    def post(self, request):
        data = _form_data(request)
        if not data.get("juzuu_aliyohifadhi"):
            data["juzuu_aliyohifadhi"] = 1
        if not data.get("tarehe_ya_kujiunga"):
            data["tarehe_ya_kujiunga"] = date.today().isoformat()
        form = MwanafunziForm(data=data, files=request.FILES)
        if not form.is_valid():
            return Response(_form_errors(form), status=400)
        mwanafunzi = form.save()
        return Response(
            {
                "id": mwanafunzi.id,
                "jina_kamili": mwanafunzi.jina_kamili,
                "namba_ya_usajili": mwanafunzi.namba_ya_usajili,
                "tarehe_ya_kujiunga": mwanafunzi.tarehe_ya_kujiunga.isoformat()
                if mwanafunzi.tarehe_ya_kujiunga
                else None,
            },
            status=201,
        )


class UsajiliMwalimuCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MANAGE_STUDENTS

    def post(self, request):
        form = MwalimuCreateForm(data=_form_data(request), files=request.FILES)
        if not form.is_valid():
            return Response(_form_errors(form), status=400)
        mwalimu = form.save()
        return Response(
            {
                "id": mwalimu.id,
                "username": mwalimu.user.username,
                "jina": str(mwalimu),
                "cheo": mwalimu.cheo,
            },
            status=201,
        )


class UsajiliSomoCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MANAGE_STUDENTS

    def post(self, request):
        form = SomoForm(data=_form_data(request))
        if not form.is_valid():
            return Response(_form_errors(form), status=400)
        somo = form.save()
        return Response(
            {
                "id": somo.id,
                "jina": somo.jina,
                "ni_la_hifdhu": somo.ni_la_hifdhu,
            },
            status=201,
        )


class UsajiliDarasaCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MANAGE_STUDENTS

    def post(self, request):
        form = DarasaForm(data=_form_data(request))
        if not form.is_valid():
            return Response(_form_errors(form), status=400)
        darasa = form.save()
        return Response(
            {"id": darasa.id, "jina": darasa.jina, "maelezo": darasa.maelezo},
            status=201,
        )
