# description: Maps each head to its nearest (or overlapped) gene.
# in: pardir/'genome_annotation/head_annotations.gff3'
# in: pardir/'genome_annotation/gene_annotations.gff3'
# out: pardir/'genome_annotation/head_genes_relations.tsv'

# out: pardir/'genome_annotation/head_genes_relations_unconsidering_sense.tsv'

from utils import (pardir, overlaps,
                   redo_flag, parse_gff_attributes,
                   prinf, GFF3_COLUMNS, safe_open)
import pandas as pd
from sys import argv
from tqdm import tqdm

# Achar genes sobrepostos (ou o mais próximo se não se sobrepuserem), às heads pra correlacionar as expressões
# em um script posterior. Gera tsv em outpath.
# LEGENDA: gene está à dir(direita)/esq(esquerda)/olap(overlappado com) a head, considerado a fita + e o sentido de escrita.

GFF_COLS_SUBSET = ['seqid', 'start', 'end', 'strand', 'attributes']

# sequid é o nome do cromossomo (contig)
# if '--sem-sentido' in argv:
COLS_TO_GROUP = 'seqid'
#     nosense_flag = '_unconsidering_sense'

# else:
#     print('Estamos considerando sentido por default (--sem-sentido para não considerar).')
#     COLS_TO_GROUP = ['seqid', 'strand']
#     nosense_flag = ''

# outpath = pardir/f'genome_annotation/head_genes_relations{nosense_flag}.tsv'
outpath = pardir/f'genome_annotation/head_genes_relations.tsv'
outfile = safe_open(outpath, exist_ok='exit')

heads = pd.read_table(pardir/'genome_annotation/head_annotations.gff3', names=GFF3_COLUMNS, usecols=GFF_COLS_SUBSET)
genes = pd.read_table(pardir/'genome_annotation/gene_annotations.gff3', names=GFF3_COLUMNS, usecols=GFF_COLS_SUBSET)
heads['id'] = parse_gff_attributes(heads.attributes).index
# Below: ID (instead of Name) should be default, but comes with 'gene:' prefix.
genes['id'] = parse_gff_attributes(genes.attributes).index
head_groups = heads.groupby(COLS_TO_GROUP)

# ### Houve genes duplicados em alugm momento, as linhas abaixo resolveriam isso. 
# genes.loc[genes.duplicated('start', 'last'), 'start'] += 1
# genes.loc[genes.duplicated('end', 'last'), 'end'] += 1

gene_groups = genes.groupby(COLS_TO_GROUP)


if __name__ == '__main__':
    # write header
    outfile.write('\t'.join(['head_id', 'gene_id', 'flag', 'distance'])+'\n')
    print('Iterate for each contig and for each head in contig.')

    for head_group_name, head_group in tqdm(head_groups):
        try:
            gene_group = gene_groups.get_group(head_group_name)

        except KeyError:
            prinf('Não há nenhum gene no cromossomo. As heads abaixo são "desgenadas".')
            prinf(head_group)
            continue

        for _, head_row in tqdm(list(head_group.iterrows())):

            for _, gene_row in gene_group.iterrows():
                if overlaps((gene_row.start, gene_row.end),
                            (head_row.start, head_row.end)):
                    flag = 'olap'
                    chosen_gene_id = gene_row.id
                    distance = 0
                    break

            # if none overlaps
            else:
                # b f de forward ou backfill
                distance = 9e99  # create Inf() class for that?
                for meth in ['b', 'f']:
                    fill_back = meth == 'b'
                    gene_pos = ['end', 'start'][fill_back]
                    head_pos = ['end', 'start'][not fill_back]

                    if gene_group[gene_pos].duplicated().sum():
                        raise pd.core.indexes.base.InvalidIndexError(
                            'You appear to have duplicated gene positions.'
                            'Indexes won\'t work properly.')

                    indexed_group = gene_group.sort_values(gene_pos).set_index(gene_pos)

                    try:
                        near_gene_index = indexed_group.index.get_loc(head_row[head_pos], meth+'fill')
                        gene_row = gene_group.iloc[near_gene_index]
                        new_distance = abs(gene_row[gene_pos] - head_row[head_pos])

                        if new_distance < distance:
                            chosen_gene_id = gene_row.id
                            flag = ["gh", "hg"][fill_back]
                            distance = new_distance

                    except KeyError:
                        prinf(f'Não há gene à {flag} de {head_row.id}.')

            outfile.write('\t'.join([head_row.id, chosen_gene_id, flag, str(distance)])+'\n')

    print(f'\nConcluído. Relações salvas em {str(outpath)}.')

outfile.close()
