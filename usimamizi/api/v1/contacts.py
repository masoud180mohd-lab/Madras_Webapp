"""Parent contacts, call log, and WhatsApp campaign for the staff API."""

from __future__ import annotations

from django.db.models import Max, Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from usimamizi.api.permissions import HasCapability
from usimamizi.api.v1.serializers import (
    MawasilianoContactWriteSerializer,
    MawasilianoSerializer,
    MawasilianoWhatsAppOpenSerializer,
    RekodiSimuSerializer,
    RekodiSimuWriteSerializer,
)
from usimamizi.models import Darasa, Mwanafunzi, RekodiSimuMzazi
from usimamizi.permissions import CAP_PARENT_CONTACT
from usimamizi.views.contacts import _Q_HAKUNA_NAMBA
from usimamizi.whatsapp import (
    TEMPLATE_CHOICES,
    WHATSAPP_TEMPLATES,
    build_wa_me_url,
    message_for_mwanafunzi,
    normalize_phone_tz,
    parse_mzazi_slot,
    recipient_whatsapp_rows,
)

_HALI_MAWASILIANO = ("wote", "zina_namba", "bila_namba")


def _choice_rows(choices):
    return [{"value": value, "label": label} for value, label in choices]


def _blank_to_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _contact_qs():
    return (
        Mwanafunzi.objects.active()
        .select_related("darasa")
        .annotate(simu_mwisho=Max("rekodi_simu__tarehe_ya_simu"))
        .order_by("jina_kamili")
    )


def _apply_contact_search(qs, q):
    if not q:
        return qs
    return qs.filter(
        Q(jina_kamili__icontains=q)
        | Q(namba_ya_usajili__icontains=q)
        | Q(jina_la_mzazi__icontains=q)
        | Q(namba_ya_simu_mzazi__icontains=q)
        | Q(jina_la_mzazi_pili__icontains=q)
        | Q(namba_ya_simu_mzazi_pili__icontains=q)
    )


def _get_mwanafunzi(mwanafunzi_id):
    return (
        Mwanafunzi.objects.select_related("darasa")
        .annotate(simu_mwisho=Max("rekodi_simu__tarehe_ya_simu"))
        .filter(pk=mwanafunzi_id)
        .first()
    )


def _contact_detail(mwanafunzi):
    rekodi = mwanafunzi.rekodi_simu.select_related("iliyorekodiwa_na").all()[:50]
    return {
        **MawasilianoSerializer(mwanafunzi).data,
        "historia": RekodiSimuSerializer(rekodi, many=True).data,
        "chaguzi": {
            "sababu": _choice_rows(RekodiSimuMzazi.SABABU_CHOICES),
            "matokeo": _choice_rows(RekodiSimuMzazi.MATOKEO_CHOICES),
            "uhusiano": _choice_rows(Mwanafunzi.UHUSIANO_MLEZI_CHOICES),
        },
    }


def _apply_contact_fields(mwanafunzi, data):
    nullable = (
        "jina_la_mzazi",
        "namba_ya_simu_mzazi",
        "jina_la_mzazi_pili",
        "namba_ya_simu_mzazi_pili",
    )
    for field in nullable:
        if field in data:
            setattr(mwanafunzi, field, _blank_to_none(data[field]))
    for field in ("uhusiano_wa_mlezi", "uhusiano_wa_mlezi_pili"):
        if field in data:
            setattr(mwanafunzi, field, data[field] or "")
    mwanafunzi.save(
        update_fields=[
            "jina_la_mzazi",
            "uhusiano_wa_mlezi",
            "namba_ya_simu_mzazi",
            "jina_la_mzazi_pili",
            "uhusiano_wa_mlezi_pili",
            "namba_ya_simu_mzazi_pili",
        ]
    )


class MawasilianoListView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_PARENT_CONTACT

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        darasa_id = (request.query_params.get("darasa") or "").strip()
        hali = (request.query_params.get("hali") or "wote").strip()
        if hali not in _HALI_MAWASILIANO:
            hali = "wote"

        qs = _apply_contact_search(_contact_qs(), q)
        if darasa_id.isdigit():
            qs = qs.filter(darasa_id=int(darasa_id))
        if hali == "bila_namba":
            qs = qs.filter(_Q_HAKUNA_NAMBA)
        elif hali == "zina_namba":
            qs = qs.exclude(_Q_HAKUNA_NAMBA)

        simu_za_karibuni = (
            RekodiSimuMzazi.objects.select_related("mwanafunzi")
            .order_by("-tarehe_ya_simu")[:15]
        )
        return Response(
            {
                "results": MawasilianoSerializer(qs, many=True).data,
                "madarasa": [
                    {"id": row.id, "jina": row.jina}
                    for row in Darasa.objects.all().order_by("jina")
                ],
                "simu_za_karibuni": [
                    {
                        "id": row.id,
                        "mwanafunzi_id": row.mwanafunzi_id,
                        "mwanafunzi": row.mwanafunzi.jina_kamili,
                        "matokeo": row.matokeo,
                        "matokeo_jina": row.get_matokeo_display(),
                        "tarehe": row.tarehe_ya_simu.isoformat(),
                    }
                    for row in simu_za_karibuni
                ],
                "q": q,
                "darasa": darasa_id,
                "hali": hali,
            }
        )


class MawasilianoWhatsAppCampaignView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_PARENT_CONTACT

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        darasa_id = (request.query_params.get("darasa") or "").strip()
        template_key = (request.query_params.get("kigezo") or "").strip()
        ujumbe = request.query_params.get("ujumbe") or ""
        if not ujumbe and template_key in WHATSAPP_TEMPLATES:
            ujumbe = WHATSAPP_TEMPLATES[template_key]

        qs = (
            Mwanafunzi.objects.active()
            .select_related("darasa")
            .exclude(_Q_HAKUNA_NAMBA)
            .order_by("jina_kamili")
        )
        qs = _apply_contact_search(qs, q)
        if darasa_id.isdigit():
            qs = qs.filter(darasa_id=int(darasa_id))

        rows = []
        for mwanafunzi in qs:
            for item in recipient_whatsapp_rows(mwanafunzi, ujumbe):
                rows.append(
                    {
                        "mwanafunzi_id": mwanafunzi.id,
                        "jina_kamili": mwanafunzi.jina_kamili,
                        "namba_ya_usajili": mwanafunzi.namba_ya_usajili,
                        "darasa": (
                            mwanafunzi.darasa.jina if mwanafunzi.darasa_id else None
                        ),
                        "slot": item["slot"],
                        "jina_mzazi": item["jina_mzazi"],
                        "uhusiano_display": item["uhusiano_display"],
                        "namba_onyesho": item["namba_onyesho"],
                        "e164": item["e164"],
                        "wa_url": item["wa_url"],
                        "ina_namba_sahihi": item["ina_namba_sahihi"],
                    }
                )
        valid_count = sum(1 for row in rows if row["ina_namba_sahihi"])
        return Response(
            {
                "results": rows,
                "madarasa": [
                    {"id": row.id, "jina": row.jina}
                    for row in Darasa.objects.all().order_by("jina")
                ],
                "q": q,
                "darasa": darasa_id,
                "kigezo": template_key,
                "ujumbe": ujumbe,
                "template_choices": _choice_rows(TEMPLATE_CHOICES),
                "valid_count": valid_count,
                "invalid_count": len(rows) - valid_count,
            }
        )


class MawasilianoDetailView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_PARENT_CONTACT

    def get(self, request, mwanafunzi_id):
        mwanafunzi = _get_mwanafunzi(mwanafunzi_id)
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        return Response(_contact_detail(mwanafunzi))

    def put(self, request, mwanafunzi_id):
        mwanafunzi = _get_mwanafunzi(mwanafunzi_id)
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        serializer = MawasilianoContactWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _apply_contact_fields(mwanafunzi, serializer.validated_data)
        mwanafunzi = _get_mwanafunzi(mwanafunzi_id)
        return Response(_contact_detail(mwanafunzi))


class MawasilianoSimuCreateView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_PARENT_CONTACT

    def post(self, request, mwanafunzi_id):
        mwanafunzi = Mwanafunzi.objects.filter(pk=mwanafunzi_id).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        serializer = RekodiSimuWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        namba = (data.get("namba_iliyopigwa") or "").strip()
        if not namba:
            namba = mwanafunzi.namba_ya_mzazi_ya_kwanza_inayopatikana()
        row = RekodiSimuMzazi.objects.create(
            mwanafunzi=mwanafunzi,
            namba_iliyopigwa=namba,
            sababu=data["sababu"],
            matokeo=data["matokeo"],
            maelezo=data.get("maelezo") or "",
            tarehe_ya_simu=data.get("tarehe_ya_simu") or timezone.now(),
            iliyorekodiwa_na=request.user,
        )
        return Response(RekodiSimuSerializer(row).data, status=201)


class MawasilianoWhatsAppOpenView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = CAP_PARENT_CONTACT

    def post(self, request, mwanafunzi_id):
        mwanafunzi = Mwanafunzi.objects.filter(pk=mwanafunzi_id).first()
        if mwanafunzi is None:
            return Response({"detail": "Mwanafunzi hapatikani."}, status=404)
        serializer = MawasilianoWhatsAppOpenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        slot = parse_mzazi_slot(data.get("mzazi") or 1)
        namba = mwanafunzi.namba_ya_mzazi_slot(slot)
        e164 = normalize_phone_tz(namba)
        if not e164:
            return Response(
                {
                    "detail": (
                        "Namba ya simu si sahihi au haipo — "
                        "haiwezi kufungua WhatsApp."
                    )
                },
                status=400,
            )
        template_key = data.get("kigezo") or ""
        custom = data.get("ujumbe") or ""
        text = message_for_mwanafunzi(
            mwanafunzi, template_key=template_key, custom_text=custom
        )
        wa_url = build_wa_me_url(e164, text)
        RekodiSimuMzazi.objects.create(
            mwanafunzi=mwanafunzi,
            namba_iliyopigwa=namba or e164,
            sababu=RekodiSimuMzazi.SABABU_WHATSAPP,
            matokeo=RekodiSimuMzazi.MATOKEO_IMEANZISHWA,
            maelezo=(text[:500] if text else "WhatsApp imeanzishwa"),
            tarehe_ya_simu=timezone.now(),
            iliyorekodiwa_na=request.user,
        )
        return Response({"wa_url": wa_url})
