"""
Permissions personnalisées de l'API.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Lecture libre pour tous, écriture réservée aux administrateurs.

    Cette permission est utilisée sur les endpoints de contenu : le site
    public consulte les contenus sans authentification, mais seuls les
    membres de l'équipe (is_staff) peuvent créer, modifier ou supprimer.
    """

    message = "Seuls les administrateurs autorisés peuvent modifier ces contenus."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)


class IsAdminUserOrReadOnlySelf(BasePermission):
    """
    Accès réservé aux administrateurs pour les opérations d'écriture,
    lecture libre.
    """

    message = "Accès réservé aux administrateurs autorisés."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)
