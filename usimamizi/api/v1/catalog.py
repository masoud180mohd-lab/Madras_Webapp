"""Read-only directory endpoints that mirror the web sidebar."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.paginator import Paginator
from django.db import IntegrityError
from django.utils import timezone
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from usimamizi.api.permissions import HasCapability
from usimamizi.api.v1.serializers import (
    AinaMalipoSerializer,
    AinaMalipoWriteSerializer,
    MalipoCreateSerializer,
    MalipoSerializer,
    MuhulaSerializer,
    MuhulaWriteSerializer,
    MwakaSerializer,
    MwakaWriteSerializer,
    MwanafunziDetailSerializer,
    MwanafunziDirectorySerializer,
    MwalimuSerializer,
    TangazoSerializer,
    UkaguziSerializer,
)
from usimamizi.academic import (
    get_active_muhula,
    get_active_mwaka,
    set_active_muhula,
    set_active_mwaka,
)
from usimamizi.audit import andika_ukaguzi_malipo
from usimamizi.dashboard import build_dashboard_context
from usimamizi.models import (
    AinaMalipo,
    Hudhurio,
    Malipo,
    Muhula,
    MwakaWaMasomo,
    Mwalimu,
    Mwanafunzi,
    RekodiHifdhu,
    RekodiMaendeleoMchana,
    RekodiUkaguzi,
)
from usimamizi.pdf_builders import (
    build_mahudhurio_pdf_response,
    build_risiti_pdf_response,
    build_sabaq_pdf_response,
)
from usimamizi.permissions import (
    CAP_ATTENDANCE,
    CAP_FEES,
    CAP_MANAGE_STUDENTS,
    CAP_MSETO,
    CAP_PROMOTE_CLASS,
    CAP_SABAQ,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
    get_mwalimu_for_user,
    user_has_capability,
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
    active = Mwanafunzi.objects.active()
    idadi = {
        "jumla": active.count(),
        "wavulana": active.filter(jinsia="ME").count(),
        "wasichana": active.filter(jinsia="KE").count(),
    }
    return {
        "jina": raw["jina_la_mtumiaji"],
        "cheo": raw["cheo"],
        "leo": raw["leo"].isoformat(),
        "idadi_wanafunzi": idadi,
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
        return Response(
            MwalimuSerializer(qs, many=True, context={"request": request}).data
        )


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
            for token in q.split():
                qs = qs.filter(
                    Q(jina_kamili__icontains=token)
                    | Q(namba_ya_usajili__icontains=token)
                )
        darasa = request.query_params.get("darasa")
        if darasa:
            qs = qs.filter(darasa_id=darasa)
        jinsia = (request.query_params.get("jinsia") or "").strip().upper()
        if jinsia in ("ME", "KE"):
            qs = qs.filter(jinsia=jinsia)
        serializer = MwanafunziDirectorySerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)


class MwanafunziDetailView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_VIEW_STUDENTS

    def get(self, request, mwanafunzi_id):
        row = (
            Mwanafunzi.objects.select_related("darasa", "programu_ya_usiku")
            .filter(pk=mwanafunzi_id)
            .first()
        )
        if row is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        return Response(
            MwanafunziDetailSerializer(row, context={"request": request}).data
        )


class MwanafunziProfileTabView(APIView):
    """Profile tabs mirroring web (without Simu/call log)."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_VIEW_STUDENTS

    def get(self, request, mwanafunzi_id):
        mwanafunzi = (
            Mwanafunzi.objects.select_related("darasa", "programu_ya_usiku")
            .filter(pk=mwanafunzi_id)
            .first()
        )
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)

        tab = (request.query_params.get("tab") or "muhtasari").strip().lower()
        if tab == "muhtasari":
            return Response(self._muhtasari(mwanafunzi, request))
        if tab == "malipo":
            return Response(self._malipo(mwanafunzi))
        if tab == "mahudhurio":
            return Response(self._mahudhurio(mwanafunzi))
        if tab == "rekodi":
            return Response(self._rekodi(mwanafunzi))
        return Response(
            {
                "detail": "Tab si sahihi.",
                "tabs": ["muhtasari", "malipo", "mahudhurio", "rekodi"],
            },
            status=400,
        )

    def _muhtasari(self, mwanafunzi, request):
        mahudhurio_kawaida = Hudhurio.objects.filter(
            mwanafunzi=mwanafunzi, aina_ya_rekodi="Kawaida"
        )
        mahudhurio_hifdhu = Hudhurio.objects.filter(
            mwanafunzi=mwanafunzi, aina_ya_rekodi="Hifdhu"
        )
        sabaq_darasa = RekodiHifdhu.objects.filter(
            mwanafunzi=mwanafunzi, aina_ya_rekodi="Darasa"
        )
        sabaq_usiku = RekodiHifdhu.objects.filter(
            mwanafunzi=mwanafunzi, aina_ya_rekodi="Usiku"
        )
        malipo_yote = mwanafunzi.malipo_yote.all()
        jumla_malipo = (
            malipo_yote.aggregate(jumla=Sum("kiasi_kilicholipwa"))["jumla"] or 0
        )
        maendeleo_count = RekodiMaendeleoMchana.objects.filter(
            mwanafunzi=mwanafunzi
        ).count()
        return {
            "tab": "muhtasari",
            "mwanafunzi": MwanafunziDetailSerializer(
                mwanafunzi, context={"request": request}
            ).data,
            "muhtasari": {
                "jumla_malipo": str(jumla_malipo),
                "idadi_malipo": malipo_yote.count(),
                "mahudhurio_mchana": mahudhurio_kawaida.count(),
                "mahudhurio_hifdhu": mahudhurio_hifdhu.count(),
                "idadi_sabaq": sabaq_darasa.count() + sabaq_usiku.count(),
                "idadi_maendeleo": maendeleo_count,
            },
        }

    def _malipo(self, mwanafunzi):
        rows = (
            mwanafunzi.malipo_yote.select_related(
                "aina_ya_malipo",
                "aina_ya_malipo__mwaka",
                "mpokeaji",
                "iliyorekodiwa_na",
            ).order_by("-tarehe_ya_malipo")
        )
        jumla = rows.aggregate(jumla=Sum("kiasi_kilicholipwa"))["jumla"] or 0
        payload = []
        for row in rows:
            recorder = None
            if row.iliyorekodiwa_na_id:
                user = row.iliyorekodiwa_na
                recorder = user.get_full_name() or user.username
            elif row.mpokeaji_id:
                recorder = str(row.mpokeaji)
            payload.append(
                {
                    "id": row.id,
                    "tarehe": row.tarehe_ya_malipo.isoformat(),
                    "aina": row.aina_ya_malipo.lebo_kamili,
                    "kiasi": str(row.kiasi_kilicholipwa),
                    "njia": row.njia_ya_malipo,
                    "alirekodi": recorder,
                }
            )
        return {
            "tab": "malipo",
            "jumla_malipo": str(jumla),
            "malipo": payload,
        }

    def _mahudhurio(self, mwanafunzi):
        def _rows(aina):
            qs = (
                Hudhurio.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina)
                .order_by("-tarehe")[:12]
            )
            return [
                {
                    "tarehe": row.tarehe.isoformat(),
                    "yupo": row.yupo,
                    "hali": "Yupo" if row.yupo else "Hayupo",
                }
                for row in qs
            ]

        return {
            "tab": "mahudhurio",
            "kawaida": _rows("Kawaida"),
            "hifdhu": _rows("Hifdhu"),
        }

    def _rekodi(self, mwanafunzi):
        def _sabaq(aina):
            qs = (
                RekodiHifdhu.objects.filter(
                    mwanafunzi=mwanafunzi, aina_ya_rekodi=aina
                )
                .select_related("somo", "mwalimu")
                .order_by("-tarehe")[:12]
            )
            return [
                {
                    "tarehe": row.tarehe.isoformat(),
                    "sura": row.sabaq_sura or "-",
                    "hali": row.sabaq_hali or "-",
                    "somo": row.somo.jina if row.somo_id else None,
                }
                for row in qs
            ]

        maendeleo = (
            RekodiMaendeleoMchana.objects.filter(mwanafunzi=mwanafunzi)
            .select_related("somo", "mwalimu__user")
            .order_by("-tarehe")[:12]
        )
        return {
            "tab": "rekodi",
            "sabaq_darasa": _sabaq("Darasa"),
            "sabaq_usiku": _sabaq("Usiku"),
            "maendeleo_mchana": [
                {
                    "tarehe": row.tarehe.isoformat(),
                    "somo": row.somo.jina,
                    "mada": row.mada_iliyosomwa,
                    "hali": row.get_hali_display(),
                }
                for row in maendeleo
            ],
        }


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
                    "aina": "kawaida" if aina == "Kawaida" else "usiku",
                    "aina_jina": (
                        "Kawaida (mchana)"
                        if aina == "Kawaida"
                        else "Usiku (hifdhu)"
                    ),
                }
                for row in rows
            ]

        return Response(
            {
                "kuanzia": kuanzia.isoformat(),
                "chuoni": _group("Kawaida"),
                "darsa": _group("Hifdhu"),
                "sehemu": [
                    {
                        "funguo": "chuoni",
                        "jina": "Kawaida (mchana)",
                        "maelezo": "Utoro wa madrasa ya kawaida",
                    },
                    {
                        "funguo": "darsa",
                        "jina": "Usiku (hifdhu)",
                        "maelezo": "Utoro wa darsa ya usiku / hifdhu",
                    },
                ],
            }
        )


_HALI_MALIPO = ("wote", "wanaodaiwa", "waliokamilisha")
_DECIMAL_ZERO = Value(0, output_field=DecimalField(max_digits=14, decimal_places=2))
_MONEY_QUANT = Decimal("0.01")


def _money_str(value):
    amount = Decimal(str(value or 0))
    if amount == 0:
        return "0"
    return str(amount.quantize(_MONEY_QUANT))


def _aina_malipo_for_mwaka(mwaka_filter):
    qs = AinaMalipo.objects.select_related("mwaka")
    if mwaka_filter == "bila":
        qs = qs.filter(mwaka__isnull=True)
    elif mwaka_filter != "yote" and str(mwaka_filter).isdigit():
        qs = qs.filter(Q(mwaka_id=int(mwaka_filter)) | Q(mwaka__isnull=True))
    return qs.order_by(
        "-mwaka__mwaka_kuanzia",
        F("mwezi").asc(nulls_last=True),
        "jina",
    )


def _mwaka_filter_from_request(request):
    active_mwaka = get_active_mwaka()
    return request.query_params.get("mwaka") or (
        str(active_mwaka.id) if active_mwaka else "yote"
    )


class MalipoListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_FEES

    def get(self, request):
        mwaka_filter = _mwaka_filter_from_request(request)
        aina_za_malipo = _aina_malipo_for_mwaka(mwaka_filter)
        neno = (request.query_params.get("q") or "").strip()
        aina_id = (request.query_params.get("aina") or "").strip()
        darasa_filter = (request.query_params.get("darasa") or "").strip()
        hali_teule = (request.query_params.get("hali") or "wote").strip()
        if hali_teule not in _HALI_MALIPO:
            hali_teule = "wote"

        if aina_id.isdigit():
            aina_teule = AinaMalipo.objects.select_related("mwaka").filter(
                pk=int(aina_id)
            ).first()
        else:
            aina_teule = aina_za_malipo.first()

        wanafunzi = (
            Mwanafunzi.objects.active()
            .select_related("darasa")
            .order_by("jina_kamili")
        )
        if neno:
            wanafunzi = wanafunzi.filter(
                Q(jina_kamili__icontains=neno)
                | Q(namba_ya_usajili__icontains=neno)
            )
        if darasa_filter.isdigit():
            wanafunzi = wanafunzi.filter(darasa_id=int(darasa_filter))

        jumla_iliyokusanywa = 0
        idadi_waliolipa = 0
        idadi_malipo = 0
        taarifa_wanafunzi = []

        if aina_teule:
            paid_agg = Malipo.objects.filter(aina_ya_malipo=aina_teule).aggregate(
                jumla=Coalesce(
                    Sum("kiasi_kilicholipwa"),
                    _DECIMAL_ZERO,
                ),
                walio=Count("mwanafunzi", distinct=True),
                idadi=Count("id"),
            )
            jumla_iliyokusanywa = paid_agg["jumla"] or 0
            idadi_waliolipa = paid_agg["walio"] or 0
            idadi_malipo = paid_agg["idadi"] or 0

            wanafunzi = wanafunzi.annotate(
                jumla_yake=Coalesce(
                    Sum(
                        "malipo_yote__kiasi_kilicholipwa",
                        filter=Q(malipo_yote__aina_ya_malipo=aina_teule),
                    ),
                    _DECIMAL_ZERO,
                )
            )
            kinachotakiwa = aina_teule.kiasi_kinachotakiwa
            for mwanafunzi in wanafunzi:
                jumla_yake = mwanafunzi.jumla_yake or 0
                deni = kinachotakiwa - jumla_yake
                if deni <= 0:
                    hali = "Amemaliza"
                elif jumla_yake > 0:
                    hali = "Nusu"
                else:
                    hali = "Hajalipa"
                if hali_teule == "wanaodaiwa" and hali == "Amemaliza":
                    continue
                if hali_teule == "waliokamilisha" and hali != "Amemaliza":
                    continue
                taarifa_wanafunzi.append(
                    {
                        "id": mwanafunzi.id,
                        "jina_kamili": mwanafunzi.jina_kamili,
                        "namba_ya_usajili": mwanafunzi.namba_ya_usajili,
                        "darasa": mwanafunzi.darasa.jina if mwanafunzi.darasa else None,
                        "jumla_yake": _money_str(jumla_yake),
                        "deni": _money_str(deni if deni > 0 else 0),
                        "hali": hali,
                    }
                )

        malipo_qs = Malipo.objects.select_related(
            "mwanafunzi",
            "mwanafunzi__darasa",
            "aina_ya_malipo",
            "aina_ya_malipo__mwaka",
        )
        if aina_teule:
            malipo_qs = malipo_qs.filter(aina_ya_malipo=aina_teule)
        if neno:
            malipo_qs = malipo_qs.filter(
                Q(mwanafunzi__jina_kamili__icontains=neno)
                | Q(mwanafunzi__namba_ya_usajili__icontains=neno)
            )
        if darasa_filter.isdigit():
            malipo_qs = malipo_qs.filter(mwanafunzi__darasa_id=int(darasa_filter))
        malipo_qs = malipo_qs.order_by("-tarehe_ya_malipo", "-id")[:80]

        active_mwaka = get_active_mwaka()
        miaka = MwakaWaMasomo.objects.all().order_by("-mwaka_kuanzia")
        return Response(
            {
                "mwaka_filter": mwaka_filter,
                "hali": hali_teule,
                "mwaka_hai": (
                    {"id": active_mwaka.id, "jina": active_mwaka.jina}
                    if active_mwaka
                    else None
                ),
                "miaka": [
                    {"id": row.id, "jina": row.jina, "ni_hai": row.ni_hai}
                    for row in miaka
                ],
                "aina_teule": (
                    AinaMalipoSerializer(aina_teule).data if aina_teule else None
                ),
                "aina_za_malipo": AinaMalipoSerializer(aina_za_malipo, many=True).data,
                "muhtasari": {
                    "kiasi_kinachotakiwa": (
                        str(aina_teule.kiasi_kinachotakiwa) if aina_teule else None
                    ),
                    "jumla_iliyokusanywa": _money_str(jumla_iliyokusanywa),
                    "idadi_waliolipa": idadi_waliolipa,
                    "idadi_malipo": idadi_malipo,
                },
                "wanafunzi": taarifa_wanafunzi,
                "malipo": MalipoSerializer(malipo_qs, many=True).data,
            }
        )


class MwanafunziMalipoCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_FEES

    def post(self, request, mwanafunzi_id):
        mwanafunzi = Mwanafunzi.objects.filter(pk=mwanafunzi_id).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        serializer = MalipoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        aina = AinaMalipo.objects.filter(pk=data["aina_ya_malipo"]).first()
        if aina is None:
            return Response({"detail": "Aina ya malipo haipatikani."}, status=400)

        jumla_yake = (
            Malipo.objects.filter(mwanafunzi=mwanafunzi, aina_ya_malipo=aina).aggregate(
                jumla=Sum("kiasi_kilicholipwa")
            )["jumla"]
            or 0
        )
        deni = aina.kiasi_kinachotakiwa - jumla_yake
        if data["kiasi"] > deni and deni >= 0:
            return Response(
                {
                    "detail": f"Hawezi kulipa zaidi ya deni (Tsh {deni}/=).",
                },
                status=400,
            )

        mwalimu = get_mwalimu_for_user(request.user)
        malipo = Malipo.objects.create(
            mwanafunzi=mwanafunzi,
            aina_ya_malipo=aina,
            kiasi_kilicholipwa=data["kiasi"],
            njia_ya_malipo=data["njia"],
            mpokeaji=mwalimu,
            iliyorekodiwa_na=request.user,
            maelezo_ya_ziada=(data.get("maelezo") or None),
        )
        andika_ukaguzi_malipo(user=request.user, malipo=malipo)
        return Response(
            {
                "id": malipo.id,
                "aina": aina.lebo_kamili,
                "kiasi": str(malipo.kiasi_kilicholipwa),
                "njia": malipo.njia_ya_malipo,
                "tarehe": malipo.tarehe_ya_malipo.isoformat(),
            },
            status=201,
        )


class MalipoRisitiPdfView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_FEES

    def get(self, request, malipo_id):
        malipo = (
            Malipo.objects.select_related(
                "mwanafunzi", "aina_ya_malipo", "mpokeaji"
            )
            .filter(pk=malipo_id)
            .first()
        )
        if malipo is None:
            return Response({"detail": "Malipo hayapatikani."}, status=404)
        return build_risiti_pdf_response(malipo)


class MwanafunziMahudhurioPdfView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_VIEW_STUDENTS, CAP_ATTENDANCE)

    def get(self, request, mwanafunzi_id):
        mwanafunzi = Mwanafunzi.objects.filter(pk=mwanafunzi_id).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        aina = (request.query_params.get("aina") or "Darasa").strip()
        muda = (request.query_params.get("muda") or "wote").strip()
        if aina not in ("Darasa", "Usiku"):
            return Response({"detail": "Aina si sahihi (Darasa|Usiku)."}, status=400)
        return build_mahudhurio_pdf_response(mwanafunzi, aina, muda)


class MwanafunziSabaqPdfView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_VIEW_STUDENTS, CAP_SABAQ)

    def get(self, request, mwanafunzi_id):
        mwanafunzi = Mwanafunzi.objects.filter(pk=mwanafunzi_id).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        aina = (request.query_params.get("aina") or "Darasa").strip()
        muda = (request.query_params.get("muda") or "wote").strip()
        if aina not in ("Darasa", "Usiku"):
            return Response({"detail": "Aina si sahihi (Darasa|Usiku)."}, status=400)
        return build_sabaq_pdf_response(mwanafunzi, aina, muda)


class MwanafunziRipotiView(APIView):
    """Night/class report lists matching web ripoti_mwanafunzi."""

    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_VIEW_STUDENTS, CAP_SABAQ, CAP_ATTENDANCE)

    def get(self, request, mwanafunzi_id):
        mwanafunzi = Mwanafunzi.objects.filter(pk=mwanafunzi_id).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        aina = (request.query_params.get("aina") or "Usiku").strip()
        if aina not in ("Darasa", "Usiku"):
            return Response({"detail": "Aina si sahihi (Darasa|Usiku)."}, status=400)
        muda = (request.query_params.get("muda") or "wote").strip()
        if muda not in ("wote", "wiki", "mwezi_huu", "mwezi_uliopita"):
            muda = "wote"

        sabaq = (
            RekodiHifdhu.objects.filter(mwanafunzi=mwanafunzi, aina_ya_rekodi=aina)
            .prefetch_related("mapande")
            .order_by("-tarehe")
        )
        aina_hudhurio = "Kawaida" if aina == "Darasa" else "Hifdhu"
        mahudhurio = Hudhurio.objects.filter(
            mwanafunzi=mwanafunzi, aina_ya_rekodi=aina_hudhurio
        ).order_by("-tarehe")

        leo = timezone.now().date()
        if muda == "wiki":
            tangu = leo - timedelta(days=7)
            mahudhurio = mahudhurio.filter(tarehe__gte=tangu)
            sabaq = sabaq.filter(tarehe__gte=tangu)
        elif muda == "mwezi_huu":
            mahudhurio = mahudhurio.filter(tarehe__year=leo.year, tarehe__month=leo.month)
            sabaq = sabaq.filter(tarehe__year=leo.year, tarehe__month=leo.month)
        elif muda == "mwezi_uliopita":
            mwezi_uliopita = leo.month - 1 if leo.month > 1 else 12
            mwaka = leo.year if leo.month > 1 else leo.year - 1
            mahudhurio = mahudhurio.filter(tarehe__year=mwaka, tarehe__month=mwezi_uliopita)
            sabaq = sabaq.filter(tarehe__year=mwaka, tarehe__month=mwezi_uliopita)

        return Response(
            {
                "mwanafunzi": {
                    "id": mwanafunzi.id,
                    "jina_kamili": mwanafunzi.jina_kamili,
                },
                "aina": aina,
                "muda": muda,
                "mahudhurio": [
                    {
                        "tarehe": row.tarehe.isoformat(),
                        "yupo": row.yupo,
                        "hali": "Yupo" if row.yupo else "Hayupo",
                        "sababu_kama_hayupo": row.sababu_kama_hayupo or "",
                    }
                    for row in mahudhurio
                ],
                "sabaq": [
                    {
                        "id": row.id,
                        "tarehe": row.tarehe.isoformat(),
                        "sura": row.sabaq_sura or "",
                        "aya_kuanzia": row.sabaq_aya_kuanzia,
                        "aya_kuishia": row.sabaq_aya_kuishia,
                        "hali": row.sabaq_hali or "",
                        "maoni": row.maoni_ya_mwalimu or "",
                        "mapande": [
                            {
                                "sura": pande.sura,
                                "aya_kuanzia": pande.aya_kuanzia,
                                "aya_kuishia": pande.aya_kuishia,
                                "hali": pande.hali,
                            }
                            for pande in row.mapande.all()
                        ],
                    }
                    for row in sabaq
                ],
            }
        )


_MWEZI_MAJINA = dict(AinaMalipo.MWEZI_CHOICES)


def _aina_malipo_page(request, qs):
    active = get_active_mwaka()
    miaka = list(MwakaWaMasomo.objects.order_by("-mwaka_kuanzia", "-id"))
    return {
        "results": AinaMalipoSerializer(qs, many=True).data,
        "mwaka_filter": _mwaka_filter_from_request(request),
        "mwaka_hai": (
            {"id": active.id, "jina": active.jina, "ni_hai": True}
            if active
            else None
        ),
        "miaka": [
            {"id": y.id, "jina": y.jina, "ni_hai": y.ni_hai} for y in miaka
        ],
        "can_manage": user_has_capability(request.user, CAP_MANAGE_STUDENTS),
    }


def _prepare_aina_fields(data, *, instance=None):
    errors = {}
    mwaka_id = data.get("mwaka")
    mwezi = data.get("mwezi")
    jina = (data.get("jina") or "").strip()
    mwaka = None
    if mwaka_id is not None:
        mwaka = MwakaWaMasomo.objects.filter(pk=mwaka_id).first()
        if mwaka is None:
            errors["mwaka"] = ["Mwaka haupatikani."]
    if mwezi and not mwaka:
        errors["mwaka"] = [
            "Chagua mwaka wa masomo unapoweka ada ya mwezi."
        ]
    if not jina and mwezi:
        jina = f"Ada · {_MWEZI_MAJINA.get(mwezi, mwezi)}"
    elif not jina:
        errors["jina"] = ["Weka jina la aina ya ada."]
    if mwaka and mwezi:
        qs = AinaMalipo.objects.filter(mwaka=mwaka, mwezi=mwezi)
        if instance is not None:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            errors["mwezi"] = [
                f"Ada ya {_MWEZI_MAJINA.get(mwezi)} kwa {mwaka.jina} tayari ipo."
            ]
    if mwaka and jina:
        qs = AinaMalipo.objects.filter(mwaka=mwaka, jina=jina)
        if instance is not None:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            errors["jina"] = [
                f'Aina "{jina}" tayari ipo kwa {mwaka.jina}.'
            ]
    return mwaka, mwezi, jina, errors


class AinaMalipoListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_MANAGE_STUDENTS, CAP_FEES)

    def get(self, request):
        mwaka_filter = _mwaka_filter_from_request(request)
        qs = _aina_malipo_for_mwaka(mwaka_filter).annotate(
            idadi_malipo=Count("malipo")
        )
        return Response(_aina_malipo_page(request, qs))

    def post(self, request):
        if not user_has_capability(request.user, CAP_MANAGE_STUDENTS):
            return Response(
                {"detail": "Huna ruhusa ya kuunda aina ya ada."},
                status=403,
            )
        serializer = AinaMalipoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mwaka, mwezi, jina, errors = _prepare_aina_fields(
            serializer.validated_data
        )
        if errors:
            return Response(errors, status=400)
        aina = AinaMalipo.objects.create(
            jina=jina,
            mwaka=mwaka,
            mwezi=mwezi,
            kiasi_kinachotakiwa=serializer.validated_data["kiasi_kinachotakiwa"],
            maelezo=(serializer.validated_data.get("maelezo") or "").strip()
            or None,
        )
        return Response(AinaMalipoSerializer(aina).data, status=201)


class AinaMalipoDetailView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MANAGE_STUDENTS

    def put(self, request, aina_id):
        aina = AinaMalipo.objects.filter(pk=aina_id).first()
        if aina is None:
            return Response({"detail": "Aina ya ada haipatikani."}, status=404)
        serializer = AinaMalipoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mwaka, mwezi, jina, errors = _prepare_aina_fields(
            serializer.validated_data, instance=aina
        )
        if errors:
            return Response(errors, status=400)
        aina.jina = jina
        aina.mwaka = mwaka
        aina.mwezi = mwezi
        aina.kiasi_kinachotakiwa = serializer.validated_data[
            "kiasi_kinachotakiwa"
        ]
        aina.maelezo = (
            serializer.validated_data.get("maelezo") or ""
        ).strip() or None
        aina.save()
        return Response(AinaMalipoSerializer(aina).data)

    def delete(self, request, aina_id):
        aina = AinaMalipo.objects.filter(pk=aina_id).first()
        if aina is None:
            return Response({"detail": "Aina ya ada haipatikani."}, status=404)
        if Malipo.objects.filter(aina_ya_malipo=aina).exists():
            return Response(
                {
                    "detail": (
                        f'Huwezi kufuta "{aina.jina}" — kuna malipo yaliyorekodiwa.'
                    )
                },
                status=400,
            )
        aina.delete()
        return Response(status=204)


def _mwaka_page():
    qs = MwakaWaMasomo.objects.prefetch_related("muhula").all()
    mwaka_hai = get_active_mwaka()
    muhula_hai = get_active_muhula()
    return {
        "results": MwakaSerializer(qs, many=True).data,
        "mwaka_hai": (
            {"id": mwaka_hai.id, "jina": mwaka_hai.jina, "ni_hai": True}
            if mwaka_hai
            else None
        ),
        "muhula_hai": (
            {
                "id": muhula_hai.id,
                "jina": muhula_hai.jina,
                "namba": muhula_hai.namba,
                "mwaka": muhula_hai.mwaka.jina,
                "ni_hai": True,
            }
            if muhula_hai
            else None
        ),
        "namba_choices": [
            {"value": value, "label": label}
            for value, label in Muhula.NAMBA_CHOICES
        ],
    }


class MwakaListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MSETO

    def get(self, request):
        return Response(_mwaka_page())

    def post(self, request):
        serializer = MwakaWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            mwaka = serializer.save()
        except IntegrityError:
            return Response(
                {"jina": ["Jina hili la mwaka tayari lipo."]},
                status=400,
            )
        return Response(
            MwakaSerializer(
                MwakaWaMasomo.objects.prefetch_related("muhula").get(pk=mwaka.pk)
            ).data,
            status=201,
        )


class MwakaActivateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MSETO

    def post(self, request, mwaka_id):
        mwaka = MwakaWaMasomo.objects.filter(pk=mwaka_id).first()
        if mwaka is None:
            return Response({"detail": "Mwaka haupatikani."}, status=404)
        set_active_mwaka(mwaka)
        return Response(
            MwakaSerializer(
                MwakaWaMasomo.objects.prefetch_related("muhula").get(pk=mwaka.pk)
            ).data
        )


class MuhulaCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MSETO

    def post(self, request):
        serializer = MuhulaWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            muhula = serializer.save()
        except IntegrityError:
            return Response(
                {"namba": ["Muhula huu tayari upo katika mwaka huu."]},
                status=400,
            )
        return Response(MuhulaSerializer(muhula).data, status=201)


class MuhulaActivateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_MSETO

    def post(self, request, muhula_id):
        muhula = (
            Muhula.objects.select_related("mwaka").filter(pk=muhula_id).first()
        )
        if muhula is None:
            return Response({"detail": "Muhula haupatikani."}, status=404)
        set_active_muhula(muhula)
        muhula.refresh_from_db()
        return Response(MuhulaSerializer(muhula).data)


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


class UkaguziListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capabilities = (CAP_MANAGE_STUDENTS, CAP_FEES)
    PER_PAGE = 30

    def get(self, request):
        kitendo = (request.query_params.get("kitendo") or "").strip()
        valid = {value for value, _label in RekodiUkaguzi.KITENDO_CHOICES}
        qs = RekodiUkaguzi.objects.select_related("mtumiaji").order_by(
            "-tarehe_ya_kitendo"
        )
        if kitendo in valid:
            qs = qs.filter(kitendo=kitendo)
        else:
            kitendo = ""

        paginator = Paginator(qs, self.PER_PAGE)
        try:
            page_num = int(request.query_params.get("page") or 1)
        except (TypeError, ValueError):
            page_num = 1
        page_obj = paginator.get_page(page_num)
        return Response(
            {
                "results": UkaguziSerializer(page_obj.object_list, many=True).data,
                "kitendo": kitendo,
                "kitendo_choices": [
                    {"value": value, "label": label}
                    for value, label in RekodiUkaguzi.KITENDO_CHOICES
                ],
                "count": paginator.count,
                "page": page_obj.number,
                "num_pages": paginator.num_pages,
            }
        )
