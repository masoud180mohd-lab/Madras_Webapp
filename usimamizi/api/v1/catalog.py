"""Read-only directory endpoints that mirror the web sidebar."""

from __future__ import annotations

from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from usimamizi.api.permissions import HasCapability
from usimamizi.api.v1.serializers import (
    AinaMalipoSerializer,
    MalipoSerializer,
    MawasilianoSerializer,
    MwakaSerializer,
    MwanafunziDirectorySerializer,
    MwalimuSerializer,
    TangazoSerializer,
    UkaguziSerializer,
)
from usimamizi.dashboard import build_dashboard_context
from usimamizi.models import (
    AinaMalipo,
    Malipo,
    MwakaWaMasomo,
    Mwalimu,
    Mwanafunzi,
    RekodiUkaguzi,
)
from usimamizi.permissions import (
    CAP_ATTENDANCE,
    CAP_FEES,
    CAP_MANAGE_STUDENTS,
    CAP_MSETO,
    CAP_PARENT_CONTACT,
    CAP_PROMOTE_CLASS,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
)


def _dashboard_payload(user):
    raw = build_dashboard_context(user)
    vipimo = [
        {
            "label": item["label"],
            "value": str(item["value"]),
            "hint": item.get("hint") or "",
            "tone": item.get("tone") or "ok",
        }
        for item in raw.get("vipimo", [])
    ]
    return {
        "jina": raw["jina_la_mtumiaji"],
        "cheo": raw["cheo"],
        "leo": raw["leo"].isoformat(),
        "vipimo": vipimo,
        "matangazo": TangazoSerializer(raw.get("matangazo") or [], many=True).data,
    }


class MwanzoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_dashboard_payload(request.user))


class WalimuListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_VIEW_DIRECTORY

    def get(self, request):
        qs = Mwalimu.objects.select_related("user").order_by("cheo", "id")
        return Response(MwalimuSerializer(qs, many=True).data)


class WanafunziListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_VIEW_STUDENTS

    def get(self, request):
        qs = (
            Mwanafunzi.objects.active()
            .select_related("darasa")
            .order_by("jina_kamili")
        )
        q = (request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(jina_kamili__icontains=q) | Q(namba_ya_usajili__icontains=q)
            )
        darasa = request.query_params.get("darasa")
        if darasa:
            qs = qs.filter(darasa_id=darasa)
        serializer = MwanafunziDirectorySerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)


class WatoroView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_ATTENDANCE, CAP_VIEW_STUDENTS)

    def get(self, request):
        from usimamizi.dashboard import _wiki_kuanzia
        from django.utils import timezone

        kuanzia = _wiki_kuanzia(timezone.now().date())

        def _group(aina):
            rows = (
                Mwanafunzi.objects.active()
                .filter(
                    hudhurio__tarehe__gte=kuanzia,
                    hudhurio__yupo=False,
                    hudhurio__aina_ya_rekodi=aina,
                )
                .distinct()
                .annotate(
                    idadi_ya_utoro=Count(
                        "hudhurio",
                        filter=Q(
                            hudhurio__tarehe__gte=kuanzia,
                            hudhurio__yupo=False,
                            hudhurio__aina_ya_rekodi=aina,
                        ),
                    )
                )
                .select_related("darasa")
                .order_by("-idadi_ya_utoro", "jina_kamili")
            )
            return [
                {
                    "id": row.id,
                    "jina_kamili": row.jina_kamili,
                    "darasa": row.darasa.jina if row.darasa_id else None,
                    "idadi_ya_utoro": row.idadi_ya_utoro,
                }
                for row in rows
            ]

        return Response(
            {
                "kuanzia": kuanzia.isoformat(),
                "chuoni": _group("Kawaida"),
                "darsa": _group("Hifdhu"),
            }
        )


class MalipoListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_FEES

    def get(self, request):
        qs = Malipo.objects.select_related(
            "mwanafunzi", "aina_ya_malipo", "aina_ya_malipo__mwaka"
        ).order_by("-tarehe_ya_malipo", "-id")[:80]
        return Response(MalipoSerializer(qs, many=True).data)


class AinaMalipoListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MANAGE_STUDENTS

    def get(self, request):
        qs = AinaMalipo.objects.select_related("mwaka").order_by(
            "-mwaka__mwaka_kuanzia", "mwezi", "jina"
        )
        return Response(AinaMalipoSerializer(qs, many=True).data)


class MwakaListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MSETO

    def get(self, request):
        qs = MwakaWaMasomo.objects.prefetch_related("muhula").all()
        return Response(MwakaSerializer(qs, many=True).data)


class HamishaPreviewView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_PROMOTE_CLASS

    def get(self, request):
        from usimamizi.models import Darasa

        qs = Darasa.objects.annotate(
            idadi_wanafunzi=Count(
                "mwanafunzi",
                filter=Q(mwanafunzi__amehifadhiwa=False),
            )
        ).order_by("jina")
        return Response(
            [
                {
                    "id": row.id,
                    "jina": row.jina,
                    "idadi_wanafunzi": row.idadi_wanafunzi,
                }
                for row in qs
            ]
        )


class MawasilianoListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_PARENT_CONTACT

    def get(self, request):
        qs = (
            Mwanafunzi.objects.active()
            .select_related("darasa")
            .order_by("jina_kamili")
        )
        q = (request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(jina_kamili__icontains=q)
                | Q(namba_ya_usajili__icontains=q)
                | Q(jina_la_mzazi__icontains=q)
                | Q(namba_ya_simu_mzazi__icontains=q)
            )
        return Response(MawasilianoSerializer(qs, many=True).data)


class UkaguziListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_MANAGE_STUDENTS, CAP_FEES)

    def get(self, request):
        qs = RekodiUkaguzi.objects.select_related("mtumiaji").order_by(
            "-tarehe_ya_kitendo"
        )[:60]
        return Response(UkaguziSerializer(qs, many=True).data)
