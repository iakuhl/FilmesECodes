"""Software de gestão do clube de cinema Filmes e Cubos."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("filmes-e-cubos")
except PackageNotFoundError:  # código rodando sem o pacote instalado
    __version__ = "0+desconhecida"
