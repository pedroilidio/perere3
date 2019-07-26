# description: Counts reads in each bp, in each head.
# in: pardir/'alinhamentos/SRA_vs_heads/only_mapped'
# out: pardir/'reads_by_heads_bp'
# flags: old(inneficient)

from utils import pardir, redo_flag, verbose
from time import time
from re import findall
from pickle import dump, load

indir = pardir/'alinhamentos/SRA_vs_heads/only_mapped'
outdir = pardir/'reads_by_heads_bp'


def parse_cigar(cigar):
    # Return list of positions.

    ret = []
    pos = 0
    
    for i in findall(r'\d+\w', cigar):
        num, op = int(i[:-1]), i[-1]

        if op in 'MX=':
            ret += list(range(pos, pos+num))
            pos = ret[-1]+1

        elif op in 'ND':
            pos += num

    return ret


def manual_parse_cigar(cigar):
    #better for small cigars.
    
    ret = []
    pos = 0
    num=''

    for s in cigar:
        if s in 'MX=':
            ret += list(range(pos, pos+int(num)))
            pos = ret[-1]+1
            num=''

        elif s in 'ND':
            pos += int(num)
            num=''

        else:
            num += s

    return ret


def add_read(contig, pos0, cigar):
    
    if contig not in heads_count_by_bp_hist.keys():
        heads_count_by_bp_hist[contig] = {}

    for  pos in [pos0 + i for i in parse_cigar(cigar)]:
        heads_count_by_bp_hist[contig][pos] = heads_count_by_bp_hist[contig].get(pos, 0) + 1


def manual_add_read(contig, pos0, cigar):
    #faster if several times called
    if contig not in heads_count_by_bp_hist.keys():
        heads_count_by_bp_hist[contig] = {}

    for pos in manual_parse_cigar(cigar):
        pos += pos0
        heads_count_by_bp_hist[contig][pos] = heads_count_by_bp_hist[contig].get(pos, 0) + 1

        
if __name__ == '__main__':

    for sam_path in indir.glob('*'):

        outpath = outdir/(sam_path.stem+'.json')
        t0 = time()

        if not outpath.exists() or redo_flag:
            count = 0
            heads_count_by_bp_hist = {'LASTREADLINE': 0}

        else:
            with outpath.open('r') as outfile:
                heads_count_by_bp_hist = load(outfile)

        if 'LASTREADLINE' not in heads_count_by_bp_hist.keys():
            print(f"'{outpath.name}' já existe, nada será feito.")
            continue

        # else:
        print(f"Processando arquivo '{sam_path.name}'...\n")
        with sam_path.open('r') as sam_file:

            # skip already viewed lines
            count = heads_count_by_bp_hist['LASTREADLINE']
            for i in range(count):
                next(sam_file)

            for line in sam_file:
                if not line.startswith('@'):
                    
                    row = line.split('\t')
                    if row[2] != '5':
                        add_read(row[0], int(row[1]), row[2])
                        
                    count += 1

                    if not count%1e5:

                        with outpath.open('') as outfile:
                            heads_count_by_bp_hist['LASTREADLINE'] = count
                            dump(heads_count_by_bp_hist, outfile)

                        if verbose:
                            avg_t = (time()-t0)/count
                            print(f'{count/29507334*100:.5f}%\t{avg_t:.5e} s per line\t total: {avg_t*29507334/60:.5f} min', end='\r')
                            
            print(f"\nArquivo processado. Salvando contagens em '{outpath._str}...'")

            del heads_count_by_bp_hist['LASTREADLINE']
            with outpath.open('wb') as outfile:
                dump(heads_count_by_bp_hist, outfile)

            print('Feito.')
