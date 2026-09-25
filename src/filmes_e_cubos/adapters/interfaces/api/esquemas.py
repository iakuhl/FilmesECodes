"""Esquemas (Pydantic) da API: o formato JSON de entrada e de saída.

Convenções que valem para todos os recursos:

- **Ids** são UUIDs em texto.
- **Decimais** (notas e escala de avaliação) saem como texto (`"4.5"`),
  para preservar a precisão exata que o domínio guarda; na entrada,
  aceitam número (`4.5`) ou texto (`"4.5"`).
- **Enumerações** saem em minúsculas (`"aberta"`, `"dorminhoco"`), como na
  CLI. Os espelhos `...Api` existem porque os membros das enumerações do
  domínio usam `auto()`, cujo valor é um inteiro sem sentido fora do
  código; o nome de cada membro é o mesmo nos dois lados.
- **Datas** em ISO 8601.
- **Corpos de entrada recusam campos desconhecidos**: um erro de
  digitação no nome de um campo vira 422, em vez de ser ignorado em
  silêncio.

Nenhuma validação de regra de negócio mora aqui: nome em branco, nota
fora da escala ou tamanho de rodada inválido são recusados pelo próprio
domínio, e o erro chega ao cliente pelo contrato de `erros.py`.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from filmes_e_cubos.adapters.interfaces.estrelas import media_em_estrelas
from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.entities.sorteio import Sorteio
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.media_das_notas import MediaDasNotas
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar

# --- Enumerações -------------------------------------------------------------


class StatusRodadaApi(StrEnum):
    ABERTA = "aberta"
    ENCERRADA = "encerrada"


class StatusIndicacaoApi(StrEnum):
    PENDENTE = "pendente"
    SORTEADA = "sorteada"
    ASSISTIDA = "assistida"


class TipoIndicacaoApi(StrEnum):
    NORMAL = "normal"
    DEMOCRACIA = "democracia"


class StatusAvaliacaoApi(StrEnum):
    NOTA_REGISTRADA = "nota_registrada"
    DORMINHOCO = "dorminhoco"


class StatusTemporadaOscarApi(StrEnum):
    EM_PREPARACAO = "em_preparacao"
    ABERTA_PARA_INDICACOES = "aberta_para_indicacoes"
    APURADA = "apurada"
    ENCERRADA = "encerrada"


class TipoCategoriaOscarApi(StrEnum):
    FIXA = "fixa"
    VARIAVEL = "variavel"

    def para_dominio(self) -> TipoCategoriaOscar:
        return TipoCategoriaOscar[self.name]


# --- Bases -------------------------------------------------------------------


class _Entrada(BaseModel):
    """Corpo de requisição: campos desconhecidos são recusados."""

    model_config = ConfigDict(extra="forbid")


# --- Clubes ------------------------------------------------------------------


class EscalaSaida(BaseModel):
    nota_minima: Decimal
    nota_maxima: Decimal
    passo: Decimal


class ConfiguracaoSaida(BaseModel):
    tamanho_rodada: int
    escala_avaliacao: EscalaSaida


class ClubeSaida(BaseModel):
    id: UUID
    nome: str
    configuracao: ConfiguracaoSaida

    @classmethod
    def de_dominio(cls, clube: Clube) -> ClubeSaida:
        escala = clube.configuracao.escala_avaliacao
        return cls(
            id=clube.id,
            nome=clube.nome,
            configuracao=ConfiguracaoSaida(
                tamanho_rodada=clube.configuracao.tamanho_rodada,
                escala_avaliacao=EscalaSaida(
                    nota_minima=escala.nota_minima,
                    nota_maxima=escala.nota_maxima,
                    passo=escala.passo,
                ),
            ),
        )


class EscalaEntrada(_Entrada):
    nota_minima: Decimal | None = None
    nota_maxima: Decimal | None = None
    passo: Decimal | None = None


class ConfiguracaoEntrada(_Entrada):
    tamanho_rodada: int | None = None
    escala_avaliacao: EscalaEntrada | None = None


class NovoClube(_Entrada):
    nome: str
    configuracao: ConfiguracaoEntrada | None = Field(
        default=None,
        description="Parâmetros do clube. Qualquer campo omitido usa o padrão do domínio "
        "(rodadas de 5 indicações, notas de 0,5 a 5,0 em passos de 0,5).",
    )

    def configuracao_de_dominio(self) -> ConfiguracaoClube:
        """Combina o que veio na requisição com a configuração padrão do domínio.

        A validação (tamanho positivo, escala coerente) fica a cargo dos
        próprios value objects.
        """
        padrao = ConfiguracaoClube.padrao()
        escala_padrao = padrao.escala_avaliacao
        configuracao = self.configuracao or ConfiguracaoEntrada()
        escala = configuracao.escala_avaliacao or EscalaEntrada()
        return ConfiguracaoClube(
            tamanho_rodada=(
                configuracao.tamanho_rodada
                if configuracao.tamanho_rodada is not None
                else padrao.tamanho_rodada
            ),
            escala_avaliacao=EscalaAvaliacao(
                nota_minima=(
                    escala.nota_minima
                    if escala.nota_minima is not None
                    else escala_padrao.nota_minima
                ),
                nota_maxima=(
                    escala.nota_maxima
                    if escala.nota_maxima is not None
                    else escala_padrao.nota_maxima
                ),
                passo=escala.passo if escala.passo is not None else escala_padrao.passo,
            ),
        )


# --- Membros -----------------------------------------------------------------


class MembroSaida(BaseModel):
    id: UUID
    clube_id: UUID
    nome: str
    apelido: str | None
    data_ingresso: date
    ativo: bool

    @classmethod
    def de_dominio(cls, membro: Membro) -> MembroSaida:
        return cls(
            id=membro.id,
            clube_id=membro.clube_id,
            nome=membro.nome,
            apelido=membro.apelido,
            data_ingresso=membro.data_ingresso,
            ativo=membro.ativo,
        )


class NovoMembro(_Entrada):
    nome: str
    apelido: str | None = None


# --- Filmes ------------------------------------------------------------------


class FilmeSaida(BaseModel):
    id: UUID
    titulo: str
    ano_lancamento: int | None
    diretor: str | None
    identificador_externo: str | None
    duracao_minutos: int | None

    @classmethod
    def de_dominio(cls, filme: Filme) -> FilmeSaida:
        return cls(
            id=filme.id,
            titulo=filme.titulo,
            ano_lancamento=filme.ano_lancamento,
            diretor=filme.diretor,
            identificador_externo=filme.identificador_externo,
            duracao_minutos=filme.duracao_minutos,
        )


class NovoFilme(_Entrada):
    titulo: str
    ano_lancamento: int | None = None
    diretor: str | None = None
    identificador_externo: str | None = Field(
        default=None, description="Identificador em uma base externa (IMDb, TMDB...)."
    )
    duracao_minutos: int | None = Field(default=None, description="Duração em minutos.")


class NovaDuracao(_Entrada):
    duracao_minutos: int = Field(description="Duração do filme, em minutos.")


# --- Rodadas, indicações e sorteios ------------------------------------------


class RodadaSaida(BaseModel):
    id: UUID
    clube_id: UUID
    numero: int
    status: StatusRodadaApi
    data_inicio: date
    data_encerramento: date | None

    @classmethod
    def de_dominio(cls, rodada: Rodada) -> RodadaSaida:
        return cls(
            id=rodada.id,
            clube_id=rodada.clube_id,
            numero=rodada.numero,
            status=StatusRodadaApi[rodada.status.name],
            data_inicio=rodada.data_inicio,
            data_encerramento=rodada.data_encerramento,
        )


class IndicacaoSaida(BaseModel):
    id: UUID
    rodada_id: UUID
    membro_id: UUID | None = Field(
        description="Quem indicou. `null` em indicações democracia, escolhidas em grupo."
    )
    filme_id: UUID
    tipo: TipoIndicacaoApi
    status: StatusIndicacaoApi
    data_indicacao: date

    @classmethod
    def de_dominio(cls, indicacao: Indicacao) -> IndicacaoSaida:
        return cls(
            id=indicacao.id,
            rodada_id=indicacao.rodada_id,
            membro_id=indicacao.membro_id,
            filme_id=indicacao.filme_id,
            tipo=TipoIndicacaoApi[indicacao.tipo.name],
            status=StatusIndicacaoApi[indicacao.status.name],
            data_indicacao=indicacao.data_indicacao,
        )


class NovaIndicacao(_Entrada):
    membro_id: UUID
    filme_id: UUID


class NovaIndicacaoDemocracia(_Entrada):
    filme_id: UUID


class SorteioSaida(BaseModel):
    id: UUID
    rodada_id: UUID
    indicacao_sorteada_id: UUID
    data_sorteio: datetime
    metodo: str

    @classmethod
    def de_dominio(cls, sorteio: Sorteio) -> SorteioSaida:
        return cls(
            id=sorteio.id,
            rodada_id=sorteio.rodada_id,
            indicacao_sorteada_id=sorteio.indicacao_sorteada_id,
            data_sorteio=sorteio.data_sorteio,
            metodo=sorteio.metodo,
        )


# --- Sessões e avaliações ----------------------------------------------------


class MediaSaida(BaseModel):
    """A média exata é `soma_das_notas / quantidade_de_notas`; nada é arredondado."""

    soma_das_notas: Decimal
    quantidade_de_notas: int
    estrelas: str = Field(
        description="A média como as interfaces a exibem: uma estrela por inteiro e a "
        "fração restante com denominador de 2 a 10 (ex.: `★★★⅔`)."
    )

    @classmethod
    def de_dominio(cls, media: MediaDasNotas) -> MediaSaida:
        return cls(
            soma_das_notas=media.soma,
            quantidade_de_notas=media.quantidade,
            estrelas=media_em_estrelas(media.valor),
        )


class SessaoSaida(BaseModel):
    id: UUID
    indicacao_id: UUID
    data_sessao: date
    membros_presentes: list[UUID]
    media_das_notas: MediaSaida | None = Field(
        description="`null` enquanto ninguém deu nota (dorminhocos não contam)."
    )

    @classmethod
    def de_dominio(cls, sessao: SessaoExibicao) -> SessaoSaida:
        media = sessao.media_das_notas
        return cls(
            id=sessao.id,
            indicacao_id=sessao.indicacao_id,
            data_sessao=sessao.data_sessao,
            membros_presentes=sorted(sessao.membros_presentes, key=str),
            media_das_notas=MediaSaida.de_dominio(media) if media is not None else None,
        )


class NovaSessao(_Entrada):
    membros_presentes: list[UUID] | None = Field(
        default=None,
        description="Membros presentes. Omitido (ou `null`), assume todos os membros ativos "
        "do clube; uma lista vazia registra a sessão sem nenhum presente.",
    )


class AvaliacaoSaida(BaseModel):
    id: UUID
    sessao_id: UUID
    membro_id: UUID
    status: StatusAvaliacaoApi
    nota: Decimal | None = Field(description="`null` quando o membro cochilou (dorminhoco).")
    comentario: str | None

    @classmethod
    def de_dominio(cls, avaliacao: Avaliacao) -> AvaliacaoSaida:
        return cls(
            id=avaliacao.id,
            sessao_id=avaliacao.sessao_id,
            membro_id=avaliacao.membro_id,
            status=StatusAvaliacaoApi[avaliacao.status.name],
            nota=avaliacao.nota.valor if avaliacao.nota is not None else None,
            comentario=avaliacao.comentario,
        )


class NovaAvaliacao(_Entrada):
    membro_id: UUID
    nota: Decimal | None = Field(
        description="Nota dada ao filme, dentro da escala do clube. `null` registra que o "
        "membro cochilou (dorminhoco). O campo é obrigatório mesmo assim: como cada membro "
        "avalia uma sessão uma vez só, ninguém deve virar dorminhoco por esquecimento."
    )
    comentario: str | None = None


# --- Óscar -------------------------------------------------------------------


class TemporadaSaida(BaseModel):
    id: UUID
    clube_id: UUID
    ano: int
    nome: str
    status: StatusTemporadaOscarApi
    data_evento: date | None

    @classmethod
    def de_dominio(cls, temporada: TemporadaOscar) -> TemporadaSaida:
        return cls(
            id=temporada.id,
            clube_id=temporada.clube_id,
            ano=temporada.ano,
            nome=temporada.nome,
            status=StatusTemporadaOscarApi[temporada.status.name],
            data_evento=temporada.data_evento,
        )


class NovaTemporada(_Entrada):
    ano: int | None = Field(default=None, description="Ano da edição. Padrão: o ano corrente.")
    nome: str | None = Field(
        default=None, description='Nome da edição. Padrão: "Óscar do <clube> <ano>".'
    )


class NovaDataDoEvento(_Entrada):
    data_evento: date = Field(description="Dia da cerimônia (AAAA-MM-DD).")


class CategoriaSaida(BaseModel):
    id: UUID
    temporada_id: UUID
    nome: str
    tipo: TipoCategoriaOscarApi
    descricao: str | None

    @classmethod
    def de_dominio(cls, categoria: CategoriaOscar) -> CategoriaSaida:
        return cls(
            id=categoria.id,
            temporada_id=categoria.temporada_id,
            nome=categoria.nome,
            tipo=TipoCategoriaOscarApi[categoria.tipo.name],
            descricao=categoria.descricao,
        )


class NovaCategoria(_Entrada):
    nome: str
    tipo: TipoCategoriaOscarApi = Field(
        default=TipoCategoriaOscarApi.VARIAVEL,
        description="`fixa` (se repete todo ano) ou `variavel` (exclusiva da edição).",
    )
    descricao: str | None = None


class NomeacaoSaida(BaseModel):
    id: UUID
    categoria_id: UUID
    filme_id: UUID
    indicado_por_membro_id: UUID | None = Field(
        description="Quem indicou o filme no clube e levará o troféu se ele vencer. "
        "`null` quando o filme veio de uma sessão democracia."
    )

    @classmethod
    def de_dominio(cls, nomeacao: NomeacaoOscar) -> NomeacaoSaida:
        return cls(
            id=nomeacao.id,
            categoria_id=nomeacao.categoria_id,
            filme_id=nomeacao.filme_id,
            indicado_por_membro_id=nomeacao.indicado_por_membro_id,
        )


class NovaNomeacao(_Entrada):
    filme_id: UUID


class PedidoDeApuracao(_Entrada):
    nomeacao_vencedora_id: UUID = Field(
        description="Nomeação que o grupo escolheu como vencedora. O mecanismo de apuração "
        "ainda está em aberto no produto, então a API não decide: registra a escolha."
    )
    membro_vencedor_id: UUID | None = Field(
        default=None,
        description="Quem leva o troféu quando a nomeação vencedora veio de uma sessão "
        "democracia (sem membro indicador). Ignorado nos demais casos.",
    )


class TrofeuSaida(BaseModel):
    id: UUID
    categoria_id: UUID
    nomeacao_vencedora_id: UUID
    membro_vencedor_id: UUID
    data_apuracao: date

    @classmethod
    def de_dominio(cls, trofeu: Trofeu) -> TrofeuSaida:
        return cls(
            id=trofeu.id,
            categoria_id=trofeu.categoria_id,
            nomeacao_vencedora_id=trofeu.nomeacao_vencedora_id,
            membro_vencedor_id=trofeu.membro_vencedor_id,
            data_apuracao=trofeu.data_apuracao,
        )


# --- Infraestrutura ----------------------------------------------------------


class SaudeSaida(BaseModel):
    status: Literal["ok"]
    versao: str


class Problema(BaseModel):
    """Corpo de toda resposta de erro (RFC 9457, `application/problem+json`)."""

    type: str = Field(default="about:blank", description="Sempre `about:blank`.")
    title: str = Field(description="Resumo do tipo de erro HTTP.")
    status: int = Field(description="Código HTTP da resposta.")
    detail: str = Field(description="Explicação do que aconteceu, para pessoas.")
    codigo: str = Field(
        description="Identificador estável do erro, para programas "
        '(ex.: `"rodada_ja_aberta"`, `"nota_fora_da_escala"`).'
    )
