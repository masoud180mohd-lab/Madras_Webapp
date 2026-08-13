from __future__ import annotations

from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from usimamizi.api.permissions import HasCapability
from usimamizi.api.v1.attendance import record_class_attendance
from usimamizi.api.v1.serializers import (
    DarasaSerializer,
    HudhurioSerializer,
    MahudhurioBatchSerializer,
    MeSerializer,
    MwanafunziRosterSerializer,
)
from usimamizi.models import Darasa, Hudhurio, Mwanafunzi
from usimamizi.permissions import (
    CAP_ATTENDANCE,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
    get_user_cheo,
    list_user_capabilities,
)


def _display_name(user):
    full = (user.get_full_name() or "").strip()
    return full or user.username


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = {
            "id": request.user.pk,
            "username": request.user.username,
            "jina": _display_name(request.user),
            "cheo": get_user_cheo(request.user),
            "capabilities": list_user_capabilities(request.user),
        }
        return Response(MeSerializer(payload).data)


class DarasaListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_VIEW_DIRECTORY

    def get(self, request):
        qs = Darasa.objects.all().order_by("jina")
        return Response(DarasaSerializer(qs, many=True).data)


class DarasaWanafunziView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_VIEW_STUDENTS

    def get(self, request, darasa_id):
        darasa = Darasa.objects.filter(pk=darasa_id).first()
        if darasa is None:
            return Response({"detail": "Darasa halipatikani."}, status=404)
        qs = (
            Mwanafunzi.objects.active()
            .filter(darasa=darasa)
            .order_by("jina_kamili")
        )
        serializer = MwanafunziRosterSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)


class MahudhurioView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_ATTENDANCE

    def get(self, request):
        darasa_id = request.query_params.get("darasa")
        if not darasa_id:
            return Response({"detail": "Parameta darasa inahitajika."}, status=400)
        aina = request.query_params.get("aina_ya_rekodi") or "Kawaida"
        raw_date = request.query_params.get("tarehe")
        try:
            day = date.fromisoformat(raw_date) if raw_date else date.today()
        except ValueError:
            return Response({"detail": "Tarehe si sahihi (YYYY-MM-DD)."}, status=400)

        qs = (
            Hudhurio.objects.filter(
                tarehe=day,
                aina_ya_rekodi=aina,
                mwanafunzi__darasa_id=darasa_id,
            )
            .select_related("mwanafunzi")
            .order_by("mwanafunzi__jina_kamili")
        )
        return Response(HudhurioSerializer(qs, many=True).data)

    def post(self, request):
        serializer = MahudhurioBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = record_class_attendance(
            user=request.user,
            darasa_id=data["darasa"],
            tarehe=data.get("tarehe"),
            aina_ya_rekodi=data.get("aina_ya_rekodi") or "Kawaida",
            rekodi=data["rekodi"],
        )
        return Response(result, status=201)
