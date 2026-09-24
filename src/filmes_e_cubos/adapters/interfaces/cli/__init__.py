"""Interface de linha de comando do Filmes e Cubos.

Esta camada apenas traduz entrada e saída de terminal em chamadas aos
casos de uso da camada `application` — nenhuma regra de negócio nasce
aqui. Quando um comando precisa de uma decisão que o domínio ainda não
tomou (ex.: quem vence uma categoria do Óscar), ele implementa o port
correspondente como um adapter local, nunca embutindo a regra no comando.
"""
