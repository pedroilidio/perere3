# description: Removes non-gene annotations from S. mansoni genome annotations. Calculates gene length.
# in: pardir/'genome_annotation/schistosoma_mansoni.PRJEA36577.WBPS12.annotations.gff3'
# out: pardir/'genome_annotation/gene_annotations.gff3'

from pandas import read_csv
from utils import pardir, redo_flag, GFF3_COLUMNS, unfold_gff
from wget import download
from subprocess import call
import os

#raw_annotations_path = pardir/'genome_annotation/schistosoma_mansoni.PRJEA36577.WBPS12.annotations'
annotations_path = pardir/'genome_annotation/gene_annotations.gff3'
annotations_url = ('ftp://ftp.ebi.ac.uk/pub/databases/wormbase/parasite/releases/WBPS13/species/schistosoma_mansoni/PRJEA36577/schistosoma_mansoni.PRJEA36577.WBPS13.annotations.gff3.gz')
raw_annotations_path = pardir/'genome_annotation'/annotations_url.split('/')[-1]

if not raw_annotations_path.exists() or redo_flag:
    print('Downloading gff...')
    download(annotations_url, str(raw_annotations_path))
    print(f'\nDownloaded {raw_annotations_path}. Unzipping...')
    call(f'gunzip "{raw_annotations_path}"', shell=True)
    

#============== REMOVER ANOTAÇÕES NÃO-GÊNICAS ===============#

print(f"Lendo '{str(raw_annotations_path).strip('.gz')}'...")
raw_annotations = read_csv(str(raw_annotations_path).strip('.gz'),
                           sep='\t', comment='#',
                           header=None, names=GFF3_COLUMNS)


print('Leitura encerrada. Removendo anotações não-gênicas...')

filtered_annotations = raw_annotations.loc[raw_annotations['type'] == 'gene']
filtered_annotations[['start', 'end']].astype(int, inplace=True)

lengths = filtered_annotations.end - filtered_annotations.start
filtered_annotations.loc[:, 'attributes'] += ';length=' + lengths.astype(str)

filtered_annotations.to_csv(annotations_path, sep='\t', index=False, header=None)

print(f"Anotações gênicas mantidas em '{str(annotations_path)}'.")
