-- Consultas de auditoria somente leitura — PostgreSQL/Aiven
-- Execute no SQL editor do Aiven no banco defaultdb.

-- 1. Contagem e ocupacao total
SELECT pg_size_pretty(pg_database_size(current_database())) AS tamanho_banco;
SELECT relname AS tabela, pg_size_pretty(pg_total_relation_size(relid)) AS tamanho_com_indices
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- 2. Linhas (contagens exatas)
SELECT 'fato_movimentacao' AS tabela, COUNT(*) AS linhas FROM fato_movimentacao
UNION ALL SELECT 'fato_perfil', COUNT(*) FROM fato_perfil
UNION ALL SELECT 'controle_carga', COUNT(*) FROM controle_carga
UNION ALL SELECT 'dim_uf', COUNT(*) FROM dim_uf
UNION ALL SELECT 'dim_setor', COUNT(*) FROM dim_setor
UNION ALL SELECT 'dim_sexo', COUNT(*) FROM dim_sexo
UNION ALL SELECT 'dim_raca_cor', COUNT(*) FROM dim_raca_cor
UNION ALL SELECT 'dim_faixa_etaria', COUNT(*) FROM dim_faixa_etaria
UNION ALL SELECT 'dim_tipo_movimentacao', COUNT(*) FROM dim_tipo_movimentacao;

-- 3. Saldos, periodos, integridade basica
SELECT 'fato_movimentacao' AS tabela, MIN(competencia) AS inicio,
 MAX(competencia) AS fim, COUNT(*) FILTER (WHERE competencia IS NULL) AS datas_nulas,
 COUNT(*) FILTER (WHERE saldo IS DISTINCT FROM (qtd_admissoes-qtd_desligamentos)) AS saldos_inconsistentes
FROM fato_movimentacao
UNION ALL
SELECT 'fato_perfil', MIN(competencia), MAX(competencia),
 COUNT(*) FILTER (WHERE competencia IS NULL),
 COUNT(*) FILTER (WHERE saldo IS DISTINCT FROM (qtd_admissoes-qtd_desligamentos))
FROM fato_perfil;

-- 4. Totais comparados: diferenca idealmente zero entre fatos para medidas aditivas
SELECT 'fato_movimentacao' AS tabela, SUM(qtd_admissoes) AS admissoes,
 SUM(qtd_desligamentos) AS desligamentos, SUM(saldo) AS saldo
FROM fato_movimentacao
UNION ALL
SELECT 'fato_perfil', SUM(qtd_admissoes), SUM(qtd_desligamentos), SUM(saldo)
FROM fato_perfil;

-- 5. Competencias disponiveis (periodo mensal)
SELECT DATE_TRUNC('month', competencia)::date AS mes,
 SUM(qtd_admissoes) AS admissoes, SUM(qtd_desligamentos) AS desligamentos, SUM(saldo) AS saldo
FROM fato_movimentacao GROUP BY 1 ORDER BY 1;

-- 6. Chaves estrangeiras realmente declaradas no banco
SELECT conrelid::regclass AS tabela, conname AS restricao,
 pg_get_constraintdef(oid) AS definicao
FROM pg_constraint WHERE contype = 'f' AND connamespace = 'public'::regnamespace
ORDER BY 1,2;

-- 7. Arquivos de origem registrados por tipo
SELECT tipo, COUNT(*) AS arquivos, SUM(linhas_lidas) AS linhas_origem
FROM controle_carga GROUP BY tipo ORDER BY tipo;
