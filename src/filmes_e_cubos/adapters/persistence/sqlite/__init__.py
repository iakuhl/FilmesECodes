"""Persistência em SQLite via SQLAlchemy Core.

Usa SQLAlchemy Core (tabelas + SQL explícito), não o ORM declarativo: as
entidades de domínio já são classes ricas, com construtores e invariantes
próprios, e não deveriam ser moldadas pela persistência. Cada repositório
aqui converte manualmente entre entidade e linha de tabela.
"""
