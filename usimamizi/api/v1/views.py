from __future__ import annotations

from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone
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
    MsetoCreateSerializer,
    MtihaniCreateSerializer,
    MtihaniSerializer,
    MwanafunziRosterSerializer,
    NyenzoSerializer,
    SabaqCreateSerializer,
    SomoSerializer,
)
from usimamizi.models import (
    Darasa,
    Hudhurio,
    Matokeo,
    MsetoMtihani,
    Mtihani,
    Muhula,
    Mwanafunzi,
    Nyenzo,
    PandeMurajaa,
    RekodiHifdhu,
    RekodiMaendeleoMchana,
    Somo,
    validate_nyenzo,
)
from usimamizi.pdf_builders import (
    build_matokeo_jumla_pdf_response,
    build_matokeo_pdf_response,
)
from usimamizi.permissions import (
    CAP_ATTENDANCE,
    CAP_EXAMS,
    CAP_MATERIALS,
    CAP_MSETO,
    CAP_SABAQ,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
    get_mwalimu_for_user,
    get_user_cheo,
    list_user_capabilities,
    user_has_capability,
)
from usimamizi.utils import hesabu_daraja, jenga_ripoti_jumla


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
            ),
            wavulana=Count(
                "mwanafunzi",
                filter=Q(
                    mwanafunzi__amehifadhiwa=False,
                    mwanafunzi__jinsia="ME",
                ),
            ),
            wasichana=Count(
                "mwanafunzi",
                filter=Q(
                    mwanafunzi__amehifadhiwa=False,
                    mwanafunzi__jinsia="KE",
                ),
            ),
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


class SomoWanafunziView(APIView):
    """Active roster of a night (Hifdhu) subject, for the Hifdhu roll call."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_VIEW_STUDENTS

    def get(self, request, somo_id):
        somo = Somo.objects.filter(pk=somo_id, ni_la_hifdhu=True).first()
        if somo is None:
            return Response({"detail": "Somo la Hifdhu halipatikani."}, status=404)
        qs = (
            Mwanafunzi.objects.active()
            .filter(programu_ya_usiku=somo)
            .order_by("jina_kamili")
        )
        serializer = MwanafunziRosterSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)


class SomoMaendeleoRosterView(APIView):
    """Active roster of a day-class subject with latest Maendeleo ya Mchana."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_VIEW_STUDENTS, CAP_SABAQ, CAP_EXAMS)

    def get(self, request, somo_id):
        somo = (
            Somo.objects.select_related("darasa")
            .filter(pk=somo_id, ni_la_hifdhu=False)
            .first()
        )
        if somo is None:
            return Response({"detail": "Somo la darasa halipatikani."}, status=404)

        qs = Mwanafunzi.objects.active()
        if somo.darasa_id:
            qs = qs.filter(darasa_id=somo.darasa_id)
        wanafunzi = list(qs.order_by("jina_kamili"))
        rows_data = MwanafunziRosterSerializer(
            wanafunzi, many=True, context={"request": request}
        ).data

        latest_by_student = {}
        for rec in (
            RekodiMaendeleoMchana.objects.filter(
                somo=somo, mwanafunzi__in=wanafunzi
            )
            .order_by("-tarehe", "-id")
        ):
            if rec.mwanafunzi_id not in latest_by_student:
                latest_by_student[rec.mwanafunzi_id] = {
                    "tarehe": rec.tarehe.isoformat(),
                    "mada_iliyosomwa": rec.mada_iliyosomwa,
                    "ukurasa_au_aya": rec.ukurasa_au_aya or "",
                    "hali": rec.hali,
                    "hali_jina": rec.get_hali_display(),
                    "maoni": rec.maoni or "",
                }

        for item in rows_data:
            item["maendeleo_mwisho"] = latest_by_student.get(item["id"])
        return Response(rows_data)


class SomoMwanafunziMaendeleoView(APIView):
    """Day-class progress report for a student in a subject (web: ripoti_maendeleo_mchana)."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_VIEW_STUDENTS, CAP_SABAQ)

    def get(self, request, somo_id, mwanafunzi_id):
        somo = Somo.objects.select_related("darasa").filter(pk=somo_id).first()
        if somo is None:
            return Response({"detail": "Somo halipatikani."}, status=404)
        mwanafunzi = Mwanafunzi.objects.filter(pk=mwanafunzi_id).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)

        muda = (request.query_params.get("muda") or "wote").strip()
        if muda not in ("wote", "wiki", "mwezi_huu", "mwezi_uliopita"):
            muda = "wote"

        rekodi_qs = (
            RekodiMaendeleoMchana.objects.filter(
                mwanafunzi=mwanafunzi, somo=somo
            )
            .select_related("mwalimu__user")
            .order_by("-tarehe", "-id")
        )
        leo = timezone.now().date()
        if muda == "wiki":
            rekodi_qs = rekodi_qs.filter(tarehe__gte=leo - timedelta(days=7))
        elif muda == "mwezi_huu":
            rekodi_qs = rekodi_qs.filter(
                tarehe__year=leo.year, tarehe__month=leo.month
            )
        elif muda == "mwezi_uliopita":
            mwezi_uliopita = leo.month - 1 if leo.month > 1 else 12
            mwaka = leo.year if leo.month > 1 else leo.year - 1
            rekodi_qs = rekodi_qs.filter(
                tarehe__year=mwaka, tarehe__month=mwezi_uliopita
            )

        return Response(
            {
                "mwanafunzi": {
                    "id": mwanafunzi.id,
                    "jina_kamili": mwanafunzi.jina_kamili,
                    "namba_ya_usajili": mwanafunzi.namba_ya_usajili,
                },
                "somo": {
                    "id": somo.id,
                    "jina": somo.jina,
                    "darasa_jina": somo.darasa.jina if somo.darasa_id else None,
                },
                "muda": muda,
                "rekodi": [
                    {
                        "id": r.id,
                        "tarehe": r.tarehe.isoformat(),
                        "mada_iliyosomwa": r.mada_iliyosomwa,
                        "ukurasa_au_aya": r.ukurasa_au_aya or "",
                        "hali": r.hali,
                        "hali_jina": r.get_hali_display(),
                        "maoni": r.maoni or "",
                        "mwalimu": str(r.mwalimu) if r.mwalimu_id else "",
                    }
                    for r in rekodi_qs
                ],
            }
        )


class MahudhurioView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_ATTENDANCE

    def get(self, request):
        darasa_id = request.query_params.get("darasa")
        somo_id = request.query_params.get("somo")
        if not darasa_id and not somo_id:
            return Response(
                {"detail": "Parameta darasa au somo inahitajika."}, status=400
            )
        if not (somo_id or darasa_id).isdigit():
            return Response({"detail": "Kitambulisho si sahihi."}, status=400)
        default_aina = "Hifdhu" if somo_id else "Kawaida"
        aina = request.query_params.get("aina_ya_rekodi") or default_aina
        raw_date = request.query_params.get("tarehe")
        try:
            day = date.fromisoformat(raw_date) if raw_date else date.today()
        except ValueError:
            return Response({"detail": "Tarehe si sahihi (YYYY-MM-DD)."}, status=400)

        qs = Hudhurio.objects.filter(tarehe=day, aina_ya_rekodi=aina)
        if somo_id:
            qs = qs.filter(mwanafunzi__programu_ya_usiku_id=somo_id)
        else:
            qs = qs.filter(mwanafunzi__darasa_id=darasa_id)
        qs = (
            qs.select_related("mwanafunzi")
            .order_by("mwanafunzi__jina_kamili")
        )
        return Response(HudhurioSerializer(qs, many=True).data)

    def post(self, request):
        serializer = MahudhurioBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = record_class_attendance(
            user=request.user,
            darasa_id=data.get("darasa"),
            tarehe=data.get("tarehe"),
            aina_ya_rekodi=data.get("aina_ya_rekodi") or "Kawaida",
            rekodi=data["rekodi"],
            somo_id=data.get("somo"),
        )
        return Response(result, status=201)


class SomoListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_VIEW_DIRECTORY, CAP_EXAMS, CAP_MATERIALS)

    def get(self, request):
        qs = Somo.objects.select_related("darasa", "mwalimu", "mwalimu__user").order_by(
            "jina"
        )
        darasa_id = request.query_params.get("darasa")
        if darasa_id:
            qs = qs.filter(darasa_id=darasa_id)
        return Response(SomoSerializer(qs, many=True).data)


class SomoDetailView(APIView):
    """Subject hub like web: header + nyenzo + mitihani + miseto choices."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_VIEW_DIRECTORY, CAP_EXAMS, CAP_MATERIALS)

    def get(self, request, somo_id):
        somo = (
            Somo.objects.select_related("darasa", "mwalimu", "mwalimu__user")
            .filter(pk=somo_id)
            .first()
        )
        if somo is None:
            return Response({"detail": "Somo halipatikani."}, status=404)
        data = SomoSerializer(somo).data
        data["nyenzo"] = NyenzoSerializer(
            Nyenzo.objects.filter(somo=somo).order_by("-tarehe_iliyowekwa"),
            many=True,
            context={"request": request},
        ).data
        data["mitihani"] = MtihaniSerializer(
            Mtihani.objects.filter(somo=somo).order_by("-tarehe", "-id"),
            many=True,
        ).data
        if somo.darasa_id and not somo.ni_la_hifdhu:
            data["miseto"] = [
                {
                    "id": m.id,
                    "jina": m.jina,
                    "tarehe": m.tarehe.isoformat(),
                }
                for m in MsetoMtihani.objects.filter(darasa_id=somo.darasa_id).order_by(
                    "-tarehe", "-id"
                )
            ]
        else:
            data["miseto"] = []
        return Response(data)


class SomoNyenzoCreateView(APIView):
    """Upload learning material for a subject (web: Pakia Nyenzo)."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MATERIALS

    def post(self, request, somo_id):
        somo = Somo.objects.filter(pk=somo_id).first()
        if somo is None:
            return Response({"detail": "Somo halipatikani."}, status=404)
        if somo.ni_la_hifdhu:
            return Response(
                {"detail": "Nyenzo zinapakwa kwenye somo la darasa tu."},
                status=400,
            )
        jina = (request.data.get("jina_la_faili") or "").strip()
        faili = request.FILES.get("faili")
        if not jina:
            return Response({"detail": "Jina la faili linahitajika."}, status=400)
        if faili is None:
            return Response({"detail": "Faili linahitajika."}, status=400)
        try:
            validate_nyenzo(faili)
        except ValidationError as exc:
            message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            return Response({"detail": message}, status=400)
        row = Nyenzo.objects.create(somo=somo, jina_la_faili=jina[:200], faili=faili)
        return Response(
            NyenzoSerializer(row, context={"request": request}).data,
            status=201,
        )


class SomoMtihaniCreateView(APIView):
    """Create exam under a subject (web: Mtihani Mpya)."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_EXAMS

    def post(self, request, somo_id):
        somo = Somo.objects.filter(pk=somo_id).first()
        if somo is None:
            return Response({"detail": "Somo halipatikani."}, status=404)
        if somo.ni_la_hifdhu:
            return Response(
                {"detail": "Mitihani inaongezwa kwenye somo la darasa tu."},
                status=400,
            )
        serializer = MtihaniCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mseto = None
        mseto_id = data.get("mseto")
        if mseto_id is not None:
            mseto = MsetoMtihani.objects.filter(pk=mseto_id).first()
            if mseto is None:
                return Response({"detail": "Mseto haupatikani."}, status=400)
            if somo.darasa_id and mseto.darasa_id != somo.darasa_id:
                return Response(
                    {"detail": "Mseto si wa darasa la somo hili."},
                    status=400,
                )
        exam = Mtihani.objects.create(
            somo=somo,
            jina_la_mtihani=data["jina_la_mtihani"],
            tarehe=data["tarehe"],
            mseto=mseto,
        )
        return Response(MtihaniSerializer(exam).data, status=201)


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
        mapande_rows = data.get("mapande") or []
        if aina == "Usiku" and mapande_rows:
            PandeMurajaa.objects.bulk_create(
                [
                    PandeMurajaa(
                        rekodi_kuu=rekodi,
                        sura=p["sura"].strip(),
                        aya_kuanzia=p.get("aya_kuanzia"),
                        aya_kuishia=p.get("aya_kuishia"),
                        hali=p.get("hali") or "Pasi",
                    )
                    for p in mapande_rows
                    if (p.get("sura") or "").strip()
                ]
            )
        return Response(
            {
                "id": rekodi.id,
                "mwanafunzi": mwanafunzi.id,
                "aina_ya_rekodi": rekodi.aina_ya_rekodi,
                "tarehe": rekodi.tarehe.isoformat(),
                "idadi_mapande": rekodi.mapande.count(),
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
        rekodi = []
        for student in wanafunzi:
            maksi = existing.get(student.id)
            row = {
                "mwanafunzi": student.id,
                "jina_kamili": student.jina_kamili,
                "namba_ya_usajili": student.namba_ya_usajili,
                "maksi": maksi,
                "daraja": None,
                "maelezo": None,
            }
            if maksi is not None:
                daraja, maelezo, _ = hesabu_daraja(maksi)
                row["daraja"] = daraja
                row["maelezo"] = maelezo
            rekodi.append(row)
        rekodi.sort(
            key=lambda r: (
                r["maksi"] is None,
                -(r["maksi"] or 0),
                r["jina_kamili"],
            )
        )
        return Response(
            {
                "mtihani": MtihaniSerializer(mtihani).data,
                "rekodi": rekodi,
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


class MtihaniMatokeoPdfView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_EXAMS

    def get(self, request, mtihani_id):
        mtihani = (
            Mtihani.objects.select_related("somo")
            .filter(pk=mtihani_id)
            .first()
        )
        if mtihani is None:
            return Response({"detail": "Mtihani haupatikani."}, status=404)
        return build_matokeo_pdf_response(mtihani)


class DarasaMsetoListCreateView(APIView):
    """Combined exam sets (MsetoMtihani) for a class (web: mseto_mitihani_darasa)."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_MSETO, CAP_EXAMS)

    def get(self, request, darasa_id):
        darasa = Darasa.objects.filter(pk=darasa_id).first()
        if darasa is None:
            return Response({"detail": "Darasa halipatikani."}, status=404)
        masomo_count = Somo.objects.filter(
            darasa=darasa, ni_la_hifdhu=False
        ).count()
        mseto_zote = (
            MsetoMtihani.objects.filter(darasa=darasa)
            .select_related("muhula", "muhula__mwaka")
            .annotate(idadi_mitihani=Count("mitihani"))
            .order_by("-tarehe", "-id")
        )
        muhula_choices = [
            {
                "id": m.id,
                "jina": f"{m.mwaka.jina} · {m.jina}",
                "ni_hai": m.ni_hai,
            }
            for m in Muhula.objects.select_related("mwaka").order_by(
                "-mwaka__mwaka_kuanzia", "namba"
            )
        ]
        return Response(
            {
                "darasa": {"id": darasa.id, "jina": darasa.jina},
                "masomo_count": masomo_count,
                "can_create": user_has_capability(request.user, CAP_MSETO),
                "muhula_choices": muhula_choices,
                "results": [
                    {
                        "id": m.id,
                        "jina": m.jina,
                        "tarehe": m.tarehe.isoformat(),
                        "muhula_id": m.muhula_id,
                        "muhula_jina": (
                            f"{m.muhula.mwaka.jina} · {m.muhula.jina}"
                            if m.muhula_id
                            else None
                        ),
                        "mitihani_iliyounganishwa": m.idadi_mitihani,
                        "jumla_masomo": masomo_count,
                    }
                    for m in mseto_zote
                ],
            }
        )

    def post(self, request, darasa_id):
        if not user_has_capability(request.user, CAP_MSETO):
            return Response(
                {"detail": "Huna ruhusa ya kuunda mseto wa mitihani."},
                status=403,
            )
        darasa = Darasa.objects.filter(pk=darasa_id).first()
        if darasa is None:
            return Response({"detail": "Darasa halipatikani."}, status=404)
        serializer = MsetoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        muhula = None
        if data.get("muhula"):
            muhula = Muhula.objects.filter(pk=data["muhula"]).first()
            if muhula is None:
                return Response({"detail": "Muhula haupatikani."}, status=400)
        mseto = MsetoMtihani.objects.create(
            darasa=darasa,
            jina=data["jina"].strip(),
            tarehe=data.get("tarehe") or date.today(),
            muhula=muhula,
        )
        return Response(
            {
                "id": mseto.id,
                "jina": mseto.jina,
                "tarehe": mseto.tarehe.isoformat(),
                "muhula_id": mseto.muhula_id,
            },
            status=201,
        )


class MsetoRipotiView(APIView):
    """Combined class exam ranking report (web: ripoti_jumla)."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_MSETO, CAP_EXAMS)

    def get(self, request, darasa_id, mseto_id):
        darasa = Darasa.objects.filter(pk=darasa_id).first()
        if darasa is None:
            return Response({"detail": "Darasa halipatikani."}, status=404)
        mseto = (
            MsetoMtihani.objects.select_related("muhula", "muhula__mwaka")
            .filter(pk=mseto_id, darasa=darasa)
            .first()
        )
        if mseto is None:
            return Response({"detail": "Mseto haupatikani."}, status=404)
        ripoti = jenga_ripoti_jumla(mseto)
        return Response(
            {
                "darasa": {"id": darasa.id, "jina": darasa.jina},
                "mseto": {
                    "id": mseto.id,
                    "jina": mseto.jina,
                    "tarehe": mseto.tarehe.isoformat(),
                    "muhula_jina": (
                        f"{mseto.muhula.mwaka.jina} · {mseto.muhula.jina}"
                        if mseto.muhula_id
                        else None
                    ),
                },
                "idadi_ya_mitihani": ripoti["idadi_ya_mitihani"],
                "masomo": [
                    {"id": s.id, "jina": s.jina} for s in ripoti["masomo"]
                ],
                "hali_ya_masomo": [
                    {
                        "somo_id": h["somo"].id,
                        "somo_jina": h["somo"].jina,
                        "mtihani_id": h["mtihani"].id if h["mtihani"] else None,
                        "mtihani_jina": (
                            h["mtihani"].jina_la_mtihani if h["mtihani"] else None
                        ),
                        "imekamilika": h["imekamilika"],
                        "idadi_maksi": h["idadi_maksi"],
                    }
                    for h in ripoti["hali_ya_masomo"]
                ],
                "grade_order": ripoti["grade_order"],
                "grade_summary": ripoti["grade_summary"],
                "matokeo_wanafunzi": [
                    {
                        "nafasi": str(row["nafasi"]),
                        "mwanafunzi_id": row["mwanafunzi"].id,
                        "jina_kamili": row["mwanafunzi"].jina_kamili,
                        "namba_ya_usajili": row["mwanafunzi"].namba_ya_usajili,
                        "jinsia": row["mwanafunzi"].jinsia,
                        "jumla": row["jumla"],
                        "wastani": row["wastani"],
                        "daraja_jumla": row["daraja_jumla"],
                        "maelezo_jumla": row["maelezo_jumla"],
                        "yaliyojazwa": row["yaliyojazwa"],
                        "masomo": [
                            {
                                "somo_id": sd["somo"].id,
                                "somo_jina": sd["somo"].jina,
                                "maksi": sd["maksi"],
                                "daraja": sd["daraja"],
                                "imejazwa": sd["imejazwa"],
                            }
                            for sd in row["masomo"]
                        ],
                    }
                    for row in ripoti["matokeo_wanafunzi"]
                ],
            }
        )


class MsetoRipotiPdfView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_MSETO, CAP_EXAMS)

    def get(self, request, darasa_id, mseto_id):
        darasa = Darasa.objects.filter(pk=darasa_id).first()
        if darasa is None:
            return Response({"detail": "Darasa halipatikani."}, status=404)
        mseto = MsetoMtihani.objects.filter(pk=mseto_id, darasa=darasa).first()
        if mseto is None:
            return Response({"detail": "Mseto haupatikani."}, status=404)
        return build_matokeo_jumla_pdf_response(darasa, mseto)


def _exam_roster(mtihani):
    somo = mtihani.somo
    qs = Mwanafunzi.objects.active()
    if somo.darasa_id:
        qs = qs.filter(darasa_id=somo.darasa_id)
    return qs.order_by("jina_kamili")
