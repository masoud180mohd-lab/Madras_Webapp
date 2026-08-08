from .permissions import (
    CAP_ATTENDANCE,
    CAP_EXAMS,
    CAP_FEES,
    CAP_MANAGE_STUDENTS,
    CAP_SABAQ,
    CAP_VIEW_DIRECTORY,
    CAP_VIEW_STUDENTS,
    user_has_capability,
)


def authz_flags(request):
    """Expose capability flags to templates for nav / CTA visibility."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    return {
        "anaweza_ona_wanafunzi": user_has_capability(user, CAP_VIEW_STUDENTS),
        "anaweza_simamia_wanafunzi": user_has_capability(user, CAP_MANAGE_STUDENTS),
        "anaweza_mahudhurio": user_has_capability(user, CAP_ATTENDANCE),
        "anaweza_sabaq": user_has_capability(user, CAP_SABAQ),
        "anaweza_mitihani": user_has_capability(user, CAP_EXAMS),
        "anaweza_malipo": user_has_capability(user, CAP_FEES),
        "anaweza_orodha": user_has_capability(user, CAP_VIEW_DIRECTORY),
    }
