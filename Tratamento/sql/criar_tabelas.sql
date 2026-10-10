-- Modelo estrela do Novo CAGED (banco "BigData", schema public)
-- Apaga e recria tudo, para que rodar de novo nao duplique dados.

DROP TABLE IF EXISTS fato_movimentacao;
DROP TABLE IF EXISTS fato_perfil;
DROP TABLE IF EXISTS controle_carga;
DROP TABLE IF EXISTS dim_uf;
DROP TABLE IF EXISTS dim_setor;
DROP TABLE IF EXISTS dim_sexo;
DROP TABLE IF EXISTS dim_raca_cor;
DROP TABLE IF EXISTS dim_faixa_etaria;
DROP TABLE IF EXISTS dim_tipo_movimentacao;

-- ---------- Dimensoes ----------

CREATE TABLE dim_uf (
    codigo    SMALLINT    PRIMARY KEY,   -- codigo IBGE da UF (99 = nao identificado)
    sigla     CHAR(2)     NOT NULL,
    nome      VARCHAR(50) NOT NULL,
    regiao    VARCHAR(20) NOT NULL
);

CREATE TABLE dim_setor (
    codigo    CHAR(1)      PRIMARY KEY,  -- secao da CNAE 2.0 (Z = nao identificado)
    descricao VARCHAR(100) NOT NULL
);

CREATE TABLE dim_sexo (
    codigo    SMALLINT    PRIMARY KEY,
    descricao VARCHAR(30) NOT NULL
);

CREATE TABLE dim_raca_cor (
    codigo    SMALLINT    PRIMARY KEY,
    descricao VARCHAR(30) NOT NULL
);

CREATE TABLE dim_faixa_etaria (
    codigo    SMALLINT    PRIMARY KEY,   -- 1 a 7 = faixas, 99 = nao identificado
    descricao VARCHAR(30) NOT NULL
);

CREATE TABLE dim_tipo_movimentacao (
    codigo    SMALLINT     PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL,
    grupo     VARCHAR(20)  NOT NULL,     -- Admissão, Desligamento ou Não identificado
    subgrupo  VARCHAR(30)  NOT NULL      -- a pedido, sem justa causa, justa causa, término de contrato, outros
);

-- ---------- Fato principal ----------
-- Uma linha por competencia x UF x setor x sexo x raca/cor x tipo de movimentacao.
-- Os valores ja estao ajustados: no prazo + fora do prazo - exclusoes.

CREATE TABLE fato_movimentacao (
    competencia        DATE     NOT NULL,   -- primeiro dia do mes da movimentacao
    uf                 SMALLINT NOT NULL REFERENCES dim_uf (codigo),
    setor              CHAR(1)  NOT NULL REFERENCES dim_setor (codigo),
    sexo               SMALLINT NOT NULL REFERENCES dim_sexo (codigo),
    raca_cor           SMALLINT NOT NULL REFERENCES dim_raca_cor (codigo),
    tipo_movimentacao  SMALLINT NOT NULL REFERENCES dim_tipo_movimentacao (codigo),
    qtd_admissoes      INTEGER  NOT NULL,
    qtd_desligamentos  INTEGER  NOT NULL,
    saldo              INTEGER  NOT NULL,
    qtd_salario_valido INTEGER  NOT NULL,
    soma_salario       NUMERIC(18, 2) NOT NULL,
    soma_horas         NUMERIC(18, 2) NOT NULL,
    PRIMARY KEY (competencia, uf, setor, sexo, raca_cor, tipo_movimentacao)
);

CREATE INDEX idx_fato_uf    ON fato_movimentacao (uf);
CREATE INDEX idx_fato_setor ON fato_movimentacao (setor);
CREATE INDEX idx_fato_tipo  ON fato_movimentacao (tipo_movimentacao);

-- ---------- Fato de perfil ----------
-- Uma linha por competencia x UF x sexo x raca/cor x faixa etaria x grupo.
-- Existe para o filtro por faixa etaria do dashboard, sem aumentar o fato principal.

CREATE TABLE fato_perfil (
    competencia        DATE        NOT NULL,
    uf                 SMALLINT    NOT NULL REFERENCES dim_uf (codigo),
    sexo               SMALLINT    NOT NULL REFERENCES dim_sexo (codigo),
    raca_cor           SMALLINT    NOT NULL REFERENCES dim_raca_cor (codigo),
    faixa_etaria       SMALLINT    NOT NULL REFERENCES dim_faixa_etaria (codigo),
    grupo              VARCHAR(12) NOT NULL CHECK (grupo IN ('Admissão', 'Desligamento')),
    qtd_admissoes      INTEGER     NOT NULL,
    qtd_desligamentos  INTEGER     NOT NULL,
    saldo              INTEGER     NOT NULL,
    qtd_salario_valido INTEGER     NOT NULL,
    soma_salario       NUMERIC(18, 2) NOT NULL,
    soma_horas         NUMERIC(18, 2) NOT NULL,
    PRIMARY KEY (competencia, uf, sexo, raca_cor, faixa_etaria, grupo)
);

CREATE INDEX idx_perfil_uf    ON fato_perfil (uf);
CREATE INDEX idx_perfil_faixa ON fato_perfil (faixa_etaria);

-- ---------- Controle de carga ----------
-- Uma linha por arquivo original: prova a origem dos dados

CREATE TABLE controle_carga (
    nome_arquivo            VARCHAR(30) PRIMARY KEY,
    tipo                    CHAR(3)     NOT NULL,   -- MOV, FOR ou EXC
    competencia_declaracao  DATE        NOT NULL,   -- mes que aparece no nome do arquivo
    linhas_lidas            INTEGER     NOT NULL,
    linhas_salario_valido   INTEGER     NOT NULL,
    saldo                   INTEGER     NOT NULL,   -- no arquivo MOV = saldo sem ajuste do mes; no EXC ja vem invertido
    data_carga              TIMESTAMP   NOT NULL
);
