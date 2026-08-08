"""
Role / capability matrix for usimamizi.

Roles (Mwalimu.cheo):
  - Mwalimu Mkuu  → full app access (explicit bypass)
  - Mwalimu wa Kawaida → teaching ops (students view, attendance, sabaq, materials, exams)
  - Jaji → exam domain (students view, exams, mseto/results)

Users without a Mwalimu profile (office/admin staff) rely on Django model permissions only.

Capability checks are enforced in views via @ruhusa_capability / user_has_capability.
"""

from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied

from .models import Mwalimu

CHEO_MKUU = "Mwalimu Mkuu"
CHEO_KAWAIDA = "Mwalimu wa Kawaida"
CHEO_JAJI = "Jaji"

CAP_VIEW_STUDENTS = "view_students"
CAP_MANAGE_STUDENTS = "manage_students"
CAP_ATTENDANCE = "attendance"
CAP_SABAQ = "sabaq"
CAP_EXAMS = "exams"
CAP_FEES = "fees"
CAP_MATERIALS = "materials"
CAP_MSETO = "mseto"
CAP_VIEW_DIRECTORY = "view_directory"  # madarasa / masomo / walimu lists

# Explicit Django model perms that grant a capability (office staff path).
PERM_CAPABILITIES = {
    CAP_VIEW_STUDENTS: (
        "usimamizi.view_mwanafunzi",
        "usimamizi.add_mwanafunzi",
        "usimamizi.change_mwanafunzi",
    ),
    CAP_MANAGE_STUDENTS: (
        "usimamizi.add_mwanafunzi",
        "usimamizi.change_mwanafunzi",
    ),
    CAP_ATTENDANCE: ("usimamizi.add_hudhurio", "usimamizi.change_hudhurio"),
    CAP_SABAQ: ("usimamizi.add_rekodihifdhu", "usimamizi.change_rekodihifdhu"),
    CAP_EXAMS: (
        "usimamizi.add_matokeo",
        "usimamizi.change_matokeo",
        "usimamizi.add_mtihani",
        "usimamizi.view_matokeo",
        "usimamizi.view_mtihani",
    ),
    CAP_FEES: (
        "usimamizi.view_malipo",
        "usimamizi.add_malipo",
        "usimamizi.change_malipo",
    ),
    CAP_MATERIALS: ("usimamizi.add_nyenzo", "usimamizi.change_nyenzo"),
    CAP_MSETO: (
        "usimamizi.add_msetomtihani",
        "usimamizi.change_msetomtihani",
        "usimamizi.view_msetomtihani",
    ),
    CAP_VIEW_DIRECTORY: (
        "usimamizi.view_darasa",
        "usimamizi.view_somo",
        "usimamizi.view_mwalimu",
    ),
}

ROLE_CAPABILITIES = {
    CHEO_MKUU: frozenset(
        {
            CAP_VIEW_STUDENTS,
            CAP_MANAGE_STUDENTS,
            CAP_ATTENDANCE,
            CAP_SABAQ,
            CAP_EXAMS,
            CAP_FEES,
            CAP_MATERIALS,
            CAP_MSETO,
            CAP_VIEW_DIRECTORY,
        }
    ),
    CHEO_KAWAIDA: frozenset(
        {
            CAP_VIEW_STUDENTS,
            CAP_ATTENDANCE,
            CAP_SABAQ,
            CAP_EXAMS,
            CAP_MATERIALS,
            CAP_VIEW_DIRECTORY,
        }
    ),
    CHEO_JAJI: frozenset(
        {
            CAP_VIEW_STUDENTS,
            CAP_EXAMS,
            CAP_MSETO,
            CAP_VIEW_DIRECTORY,
        }
    ),
}

# Legacy codenames still used by older decorators → capability (any-of).
LEGACY_PERM_TO_CAPS = {
    "usimamizi.add_hudhurio": (CAP_ATTENDANCE,),
    "usimamizi.add_mwanafunzi": (CAP_MANAGE_STUDENTS,),
    "usimamizi.change_mwanafunzi": (CAP_MANAGE_STUDENTS,),
    "usimamizi.add_nyenzo": (CAP_MATERIALS,),
    "usimamizi.add_mtihani": (CAP_EXAMS,),
    "usimamizi.add_matokeo": (CAP_EXAMS,),
    "usimamizi.change_matokeo": (CAP_EXAMS,),
    "usimamizi.add_rekodihifdhu": (CAP_SABAQ,),
    "usimamizi.add_malipo": (CAP_FEES,),
    "usimamizi.add_msetomtihani": (CAP_MSETO,),
}


def get_mwalimu_for_user(user):
    if not getattr(user, "is_authenticated", False):
        return None
    return (
        Mwalimu.objects.filter(user=user)
        .select_related("user")
        .first()
    )


def get_user_cheo(user):
    mwalimu = get_mwalimu_for_user(user)
    return mwalimu.cheo if mwalimu else None


def user_has_capability(user, *capabilities):
    """True if user may perform any of the named capabilities."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    needed = set(capabilities)
    if not needed:
        return False

    cheo = get_user_cheo(user)
    if cheo == CHEO_MKUU:
        return True
    if cheo and needed & ROLE_CAPABILITIES.get(cheo, frozenset()):
        return True

    for cap in needed:
        for perm in PERM_CAPABILITIES.get(cap, ()):
            if user.has_perm(perm):
                return True
    return False


def user_has_app_permission(user, *permissions):
    """
    Backward-compatible check used by existing views.

    Superuser / Mwalimu Mkuu → allow.
    Else: capability implied by legacy perm codenames, OR raw Django has_perm.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if get_user_cheo(user) == CHEO_MKUU:
        return True

    caps = set()
    for perm in permissions:
        caps.update(LEGACY_PERM_TO_CAPS.get(perm, ()))
    if caps and user_has_capability(user, *caps):
        return True
    return any(user.has_perm(permission) for permission in permissions)


def ruhusa_inahitajika(*permissions):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if user_has_app_permission(request.user, *permissions):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator


def ruhusa_capability(*capabilities):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if user_has_capability(request.user, *capabilities):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator


def require_linked_mwalimu(request, redirect_to="mwanzo"):
    """
    Return linked Mwalimu or None after flashing a Swahili error.
    Use for flows that must stamp a teacher on the record (sabaq).
    """
    mwalimu = get_mwalimu_for_user(request.user)
    if mwalimu:
        return mwalimu
    messages.error(
        request,
        "Akaunti yako haijaunganishwa na wasifu wa Mwalimu. "
        "Wasiliana na Mwalimu Mkuu au admin ili kuunganisha kabla ya kurekodi sabaq.",
    )
    return None


def linked_mwalimu_or_none(user):
    """Optional teacher profile (fees may proceed with mpokeaji=None for office staff)."""
    return get_mwalimu_for_user(user)
