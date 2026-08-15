from __future__ import annotations

from datetime import date

from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from usimamizi.api.permissions import HasCapability
from usimamizi.api.v1.attendance import record_class_attendance
from usimamizi.api.v1.serializers import (
    DarasaSerializer,
    HudhurioSerializer,
    MaendeleoCreateSerializer,
    MahudhurioBatchSerializer,
    MaksiBatchSerializer,
    MeSerializer,
    MtihaniSerializer,
    MwanafunziRosterSerializer,
    SabaqCreateSerializer,
    SomoSerializer,
)
from usimamizi.models import (
    Darasa,
    Hudhurio,
    Matokeo,
    Mtihani,
    Mwanafunzi,
    RekodiHifdhu,
    RekodiMaendeleoMchana,
    Somo,
)
from usimamizi.permissions import (
    CAP_ATTENDANCE,
    CAP_EXAMS,
    CAP_SABAQ,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
    get_mwalimu_for_user,
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
        qs = Darasa.objects.annotate(
            idadi_wanafunzi=Count(
                "mwanafunzi",
                filter=Q(mwanafunzi__amehifadhiwa=False),
            )
        ).order_by("jina")
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


class SomoListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_VIEW_DIRECTORY

    def get(self, request):
        qs = Somo.objects.select_related("darasa", "mwalimu", "mwalimu__user").order_by(
            "jina"
        )
        darasa_id = request.query_params.get("darasa")
        if darasa_id:
            qs = qs.filter(darasa_id=darasa_id)
        return Response(SomoSerializer(qs, many=True).data)


class SabaqCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_SABAQ

    def post(self, request):
        mwalimu = get_mwalimu_for_user(request.user)
        if mwalimu is None:
            return Response(
                {
                    "detail": (
                        "Akaunti yako haijaunganishwa na wasifu wa Mwalimu. "
                        "Wasiliana na Mwalimu Mkuu kabla ya kurekodi sabaq."
                    )
                },
                status=403,
            )
        serializer = SabaqCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mwanafunzi = Mwanafunzi.objects.filter(pk=data["mwanafunzi"]).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        if mwanafunzi.amehifadhiwa:
            return Response(
                {"detail": "Mwanafunzi huyu amehifadhiwa — huwezi kurekodi sabaq."},
                status=400,
            )
        aina = data["aina_ya_rekodi"]
        darasa = mwanafunzi.darasa if aina == "Darasa" else None
        somo = mwanafunzi.programu_ya_usiku if aina == "Usiku" else None
        rekodi = RekodiHifdhu.objects.create(
            mwanafunzi=mwanafunzi,
            somo=somo,
            darasa=darasa,
            aina_ya_rekodi=aina,
            mwalimu=mwalimu,
            sabaq_sura=data.get("sabaq_sura") or None,
            sabaq_aya_kuanzia=data.get("sabaq_aya_kuanzia"),
            sabaq_aya_kuishia=data.get("sabaq_aya_kuishia"),
            sabaq_hali=data.get("sabaq_hali") or None,
            maoni_ya_mwalimu=data.get("maoni_ya_mwalimu") or None,
        )
        return Response(
            {
                "id": rekodi.id,
                "mwanafunzi": mwanafunzi.id,
                "aina_ya_rekodi": rekodi.aina_ya_rekodi,
                "tarehe": rekodi.tarehe.isoformat(),
            },
            status=201,
        )


class MaendeleoCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_SABAQ

    def post(self, request):
        mwalimu = get_mwalimu_for_user(request.user)
        if mwalimu is None:
            return Response(
                {
                    "detail": (
                        "Akaunti yako haijaunganishwa na wasifu wa Mwalimu. "
                        "Wasiliana na Mwalimu Mkuu kabla ya kurekodi maendeleo."
                    )
                },
                status=403,
            )
        serializer = MaendeleoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mwanafunzi = Mwanafunzi.objects.filter(pk=data["mwanafunzi"]).first()
        somo = Somo.objects.filter(pk=data["somo"]).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        if somo is None:
            return Response({"detail": "Somo halipatikani."}, status=404)
        if mwanafunzi.amehifadhiwa:
            return Response(
                {"detail": "Mwanafunzi huyu amehifadhiwa — huwezi kurekodi maendeleo."},
                status=400,
            )
        if somo.ni_la_hifdhu:
            return Response(
                {"detail": "Tumia Sabaq kwa somo la hifdhu."},
                status=400,
            )
        if somo.darasa_id and mwanafunzi.darasa_id != somo.darasa_id:
            return Response(
                {"detail": "Mwanafunzi hayuko katika darasa la somo hili."},
                status=400,
            )
        row = RekodiMaendeleoMchana.objects.create(
            mwanafunzi=mwanafunzi,
            somo=somo,
            mwalimu=mwalimu,
            mada_iliyosomwa=data["mada_iliyosomwa"],
            ukurasa_au_aya=data.get("ukurasa_au_aya") or None,
            hali=data["hali"],
            maoni=data.get("maoni") or None,
        )
        return Response(
            {
                "id": row.id,
                "mwanafunzi": mwanafunzi.id,
                "somo": somo.id,
                "hali": row.hali,
                "tarehe": row.tarehe.isoformat(),
            },
            status=201,
        )


class MtihaniListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_EXAMS

    def get(self, request):
        qs = Mtihani.objects.select_related("somo").order_by("-tarehe", "-id")
        somo_id = request.query_params.get("somo")
        if somo_id:
            qs = qs.filter(somo_id=somo_id)
        return Response(MtihaniSerializer(qs, many=True).data)


class MtihaniMatokeoView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_EXAMS

    def get(self, request, mtihani_id):
        mtihani = Mtihani.objects.select_related("somo").filter(pk=mtihani_id).first()
        if mtihani is None:
            return Response({"detail": "Mtihani haupatikani."}, status=404)
        wanafunzi = _exam_roster(mtihani)
        existing = {
            row.mwanafunzi_id: row.maksi
            for row in Matokeo.objects.filter(mtihani=mtihani, mwanafunzi__in=wanafunzi)
        }
        return Response(
            {
                "mtihani": MtihaniSerializer(mtihani).data,
                "rekodi": [
                    {
                        "mwanafunzi": student.id,
                        "jina_kamili": student.jina_kamili,
                        "namba_ya_usajili": student.namba_ya_usajili,
                        "maksi": existing.get(student.id),
                    }
                    for student in wanafunzi
                ],
            }
        )

    def put(self, request, mtihani_id):
        mtihani = Mtihani.objects.select_related("somo").filter(pk=mtihani_id).first()
        if mtihani is None:
            return Response({"detail": "Mtihani haupatikani."}, status=404)
        serializer = MaksiBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roster_ids = {student.id for student in _exam_roster(mtihani)}
        unknown = [
            row["mwanafunzi"]
            for row in serializer.validated_data["rekodi"]
            if row["mwanafunzi"] not in roster_ids
        ]
        if unknown:
            return Response(
                {"detail": "Mwanafunzi si wa mtihani huu.", "ids": unknown},
                status=400,
            )
        for row in serializer.validated_data["rekodi"]:
            Matokeo.objects.update_or_create(
                mwanafunzi_id=row["mwanafunzi"],
                mtihani=mtihani,
                defaults={"maksi": row["maksi"]},
            )
        return Response({"idadi": len(serializer.validated_data["rekodi"])})


def _exam_roster(mtihani):
    somo = mtihani.somo
    qs = Mwanafunzi.objects.active()
    if somo.darasa_id:
        qs = qs.filter(darasa_id=somo.darasa_id)
    return qs.order_by("jina_kamili")
