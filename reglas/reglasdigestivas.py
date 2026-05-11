"""Alias de compatibilidad para reglas_digestivas."""

try:
    # Permite importar este modulo como parte del paquete reglas.
    from .reglas_digestivas import *  # noqa: F401,F403
except ImportError:
    # Mantiene compatibilidad si el archivo se ejecuta o importa sin contexto de paquete.
    from reglas_digestivas import *  # type: ignore # noqa: F401,F403
