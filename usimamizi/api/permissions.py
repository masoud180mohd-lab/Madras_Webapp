"""DRF permission classes that reuse the existing CAP_* matrix."""

from rest_framework.permissions import BasePermission

from usimamizi.permissions import user_has_capability


class HasCapability(BasePermission):
    """
    Allow if the user has ``view.required_capability``.

    Set ``required_capability`` (one CAP_*) or ``required_capabilities``
    (OR of several CAP_* names) on the view.
    """

    message = "Huna ruhusa ya kitendo hiki."

    def has_permission(self, request, view):
        needed = getattr(view, "required_capabilities", None)
        if needed:
            return user_has_capability(request.user, *needed)
        capability = getattr(view, "required_capability", None)
        if not capability:
            return False
        return user_has_capability(request.user, capability)
