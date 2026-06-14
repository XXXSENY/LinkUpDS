"""
Exceptions personnalisées pour LinkUpDS API.
"""


class LinkUpException(Exception):
    """Exception de base pour LinkUpDS."""
    pass


class AuthenticationError(LinkUpException):
    """Erreur d'authentification."""
    pass


class AuthorizationError(LinkUpException):
    """Erreur d'autorisation."""
    pass


class ResourceNotFoundError(LinkUpException):
    """Ressource non trouvée."""
    pass


class ValidationError(LinkUpException):
    """Erreur de validation des données."""
    pass


class DatabaseError(LinkUpException):
    """Erreur d'accès à la base de données."""
    pass
