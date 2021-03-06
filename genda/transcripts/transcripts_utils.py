from itertools import tee
try:
    from future_builtins import zip
except ImportError: # not 2.6+ or is 3.x
    try:
        from itertools import izip as zip
    except ImportError:
        pass
import requests
# Requires bx python
from bx.intervals.intersection import Intersecter, Interval
from .diffevent import DiffEvent, EventCollection 


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return(zip(a,b))



class Exon(object):
    """ A region
    """
    def __init__(self, region, start, end):
        self.region = region
        try:
            self.start = int(start)
            self.end = int(end)
        except ValueError:
            print("start and end positions need to be integers")


def get_transcript_ids(gene, gff=None, ref37=False):
    """ Get transcript ids from Ensembl REST api
    Returns a list of transcripts,

    Arguments
    ---------
    gene - Ensembl gene ID
    gff - pysam.Tabixfile

    :TODO make out_transcripts a list of transcript class
    :TODO try GTF first and except to Ensembl otherwise
    """

    if gff:
        pass

    if ref37:
        server = "http://grch37.rest.ensembl.org/"
    else:
        server = "http://rest.ensembl.org"
    ext = "/lookup/id/{0}?species=homo_sapiens;expand=1"
    r = requests.get(server+ext.format(gene), headers={ "Content-Type" :
        "application/json"})
    out_transcripts = []
    decoded = r.json()
    for i in decoded['Transcript']:
        out_transcripts.append(i['id'])
    return(out_transcripts, 
            decoded['display_name'],
            decoded['seq_region_name'], 
            (int(decoded['start']), int(decoded['end'])))



def break_exons(exon1, exon2):
    """ 
    Returns a list of new exons by breaking an interval into 2 intervals if it overlaps, 
    upstream exon always
    comes first.

    """
    if exon1.region == exon2.region:
        if exon2.start > exon1.start and exon2.end < exon1.end:
            # Case where exon1 is wholly enclosed in exon2
            return([Exon(exon1.region, exon1.start, exon2.start),
                    Exon(exon1.region, exon2.start, exon2.end),
                    Exon(exon1.region, exon2.end, exon1.end)])
        elif exon2.end < exon1.end:
            return([Exon(exon1.region, exon1.start, exon2.start),
                    Exon(exon1.region, exon2.start, exon1.end),
                    Exon(exon1.region, exon1.end, exon2.end)])
        else:
            # Do nothing if there is no overlap
            return(exon1, exon2)
    else:
        pass


def unique_sets(set_list):
    """ 
    Returns a list of sets
    Calculates the unique regions defined such that only the same elements
    are bound to it.
    """

    # Since most exons are shared, remove the most common elements first
    common_set = reduce( lambda x, y: x & y, set_list)
    rs = [i - common_set for i in set_list]
    out_sets = []
    all_unique = True
    n = len(set_list)
    for i in set_list:
        intersection = [t & i for t in set_list]
        # uniqufy the intersections
        u_s = set(intersection)
        for t in u_s:
            pass
        set_list = [i]
    while len(rs) > 0:
        intersection = [t & i for i in set_list]
        out_sets.append(i)

    return(out_sets)


def _generate_modified_cigar(transcript, current, mskip=1):
    """
    Arguments
    ---------
    transcript : list
    current : int
    mskip : int
    """
    pass




def _get_by_exonn(exon_n, transcript):
    for i, j in enumerate(transcript):
        if j[2] == exon_n:
            return(i)
        else: pass

def _generate_cigar(transcript, current, mskip=1):
    """Generates cigar tuple

    Arguments
    ---------
    transcript : list
        an exon list
    current : int
        current exon
    mskip : int
        number of exons to skip
    """
    out = []
    for i in (range(mskip)):
        pint = transcript[current - 1 + i][0:2]  
        start, end = transcript[current + i][0:2]
        #:TODO refactor this
        try:
            nint = transcript[current + 1 + i][0:2]
            c1 = max(start-pint[1], 
                start-nint[1])
            c2 = max(nint[0] - end,
                    pint[0] - end)
            if i >= 1:
                out.extend([(0, start, end), (3, c2)])
            else:
                out.extend([(3, c1), (0, start, end), (3, c2)])
        except IndexError:
            # end
            c1 = start-pint[1]
            out.extend(([(3, c1), (0, start, end)]))
    return(out)


        
def compare_two_transcripts(trans1, trans2, transcript_dict, 
        afe=False):
    """
    Returns the splice differences between two transcripts.
    Single exon-comparisons are ignored.

    Parameters
    ----------
    trans1 : string 
        transcript of interest
    trans2 : string 
        second transcript of interest
    transcript_dict : a dictionary of transcript names with 
    values being a list of exons
    afe : bool
       whether to include alternate start and ends

    :TODO make a better return
    :TODO maybe include something similar to to_plot
    Returns
    -------
    Exclusive Junctions : 
    5' upstream exons : 
    3' downstram exons : 
    Skipped Exons : Diffevent 
    """
    # TODO refactor this
    t1 = transcript_dict[trans1]
    t2 = transcript_dict[trans2]
    tree = Intersecter()
    starts1 = [i[0] for i in t1]
    starts2 = [i[0] for i in t2]
    reverse = False
    if min(starts1) <= min(starts2):
        s1 = t1
        s2 = t2
        s2_beg = min(starts2)
    else:
        s1 = t2 
        s2 = t1
        reverse = True
        s2_beg = min(starts1)
    if reverse: torder = (trans2, trans1)
    else: torder = (trans1, trans2)
    # Ignore single-exon stuff
    if len(s1) <= 1 or len(s2) <= 1:
        return([], [])
    for i in s1:
        tree.add_interval(Interval(int(i[0]), int(i[1]), 
            value={'anno':i[2]}))
    matching_exons = []
    exclusive_juncs = []
    skipped_exons = []
    altends = []
    exon_match = {}
    s1.sort(key=lambda x: x[0])
    s2.sort(key=lambda x: x[0])
    max_exon_1 =  s1[-1][2]
    max_exon_2 = s2[-1][2]
    #end_position_s2 = max([i[1] for i in s2])
    s1_end = max([i[1] for i in s1])
    prev_match = None
    if max_exon_1 < s1[0][2]:
        strand = -1
    else:
        strand = 1
    for pcurr in range(len(s2)):
        start, end, exon_n = s2[pcurr]
        overlap = tree.find(int(start), int(end))
        if len(overlap) == 0:
            if prev_match and (start < s1_end):
                #skipped exons
                cigar = _generate_cigar(s2, pcurr, mskip=1)
                try:
                    if exon_match[exon_n - strand] == prev_match.value['anno']:
                        try:
                            nm = tree.find(*s2[pcurr + 1][0:2])[0]
                            ocigar = [(3, nm.start - prev_match.end)]
                            nexon = nm.value['anno']
                        except IndexError:
                            nm=s1[_get_by_exonn(prev_match.value['anno']+strand,s1)] 
                            ocigar = [(3,nm[0] - prev_match.end)]
                            nexon = nm[2]
                    skipped_exons.append(DiffEvent('skipped_exon', start, end,
                            torder, cigar2=cigar, cigar1 = ocigar, 
                            exon_num = (None, exon_n), 
                            exon2=(prev_match.value['anno'], nexon))
                            )
                except KeyError:
                    # Multiple skipped exons
                    ncig = _generate_cigar(s2, pcurr, mskip=1)[1:]
                    skipped_exons[-1]._extend(ncig, cig=2)
            elif start > s1_end: 
                if prev_match:
                    cigar = _generate_cigar(s2, pcurr, mskip=1)
                    pm = tree.find(*s2[pcurr - 1][0:2])[0]
                    pexon = pm.value['anno']
                    ocigar = []
                    for i in range(pexon, max_exon_1+strand, strand):
                        narg = _get_by_exonn(i, s1)
                        ocigar.append((0, s1[narg][0], s1[narg][1]))
                        try:
                            ocigar.append((3, s1[narg][1] - s1[narg+1][0]))
                        except IndexError:
                            pass
                    #:TODO extend ocigar till end?
                    altends.append(DiffEvent('AE', start, end,
                        torder, cigar2=cigar, cigar1=ocigar,
                        exon_num = (None, exon_n)))
                else: 
                    pass
            else: 
                # Alternate start site that starts in between exons
                # of other transcript
                cigar = _generate_cigar(s2, pcurr, mskip=1)[:-1]
                try:
                    nm = tree.find(*s2[pcurr + 1][0:2])[0]
                except IndexError:
                    from IPython import embed
                    embed()
                nexon = nm.value['anno']
                narg = _get_by_exonn(nexon - strand, s1)
                pmatch = s1[narg]
                ocigar = [(0, pmatch[1] - pmatch[0]),
                        (3, nm.start - pmatch[1])]
                altends.append(DiffEvent('AS', start, end,
                        torder, cigar2=cigar, cigar1 = ocigar))
        elif len(overlap) == 1:
            if start == overlap[0].start and end == overlap[0].end:
                s1_exon_n = overlap[0].value['anno']
                matching_exons.append((start, end, (s1_exon_n, 
                    exon_n), (0, 0)))
                if prev_match:
                    if s1_exon_n - prev_match.value['anno']  == strand: 
                        pass
                    else:
                        # Difference in exon matches
                        mskip = abs(s1_exon_n - prev_match.value['anno'] ) - 1
                        narg = _get_by_exonn(prev_match.value['anno']+strand, s1) 
                        s_s1 = s1[narg] # skipped s1
                        cigar = _generate_cigar(s1, narg, mskip=mskip)
                        ocigar = [(3, start - s2[pcurr-1][1])]
                        # Remove previous one
                        skipped_exons.append(
                                DiffEvent('skipped_exon', 
                                s_s1[0], s_s1[1], torder, 
                                cigar2 = ocigar, cigar1 = cigar, 
                                exon_num = (s_s1[2], None), 
                                exon2 = (exon_n-strand, exon_n)))
                prev_match = overlap[0]
            else:
                sstart = min(start, overlap[0].start)
                ssend = max(end, overlap[0].end)
                # Ignore 5' or 3' differences
                if (exon_n == max_exon_2 and
                        overlap[0].value['anno'] == max_exon_1):
                    if end == overlap[0].end:
                        prev_match = overlap[0]
                else:
                    exclusive_juncs.append(
                            (sstart, ssend,
                            (overlap[0].value['anno'], exon_n), 
                            (overlap[0].start - start, overlap[0].end - end) ))
            # Deal with partial matches
            prev_match = overlap[0]
            exon_match[exon_n] = int(overlap[0].value['anno'])
        else:
            pass
    skipped_exons = EventCollection(transcript_ids = [s1, s2], events=skipped_exons)
    skipped_exons.events.extend(altends)
    return(matching_exons, skipped_exons)


def pairwise_transcript_comparison(transcript_dict):
    """ Returns pairwise transcripts where there are skipped exons 
    and the exon that is skipped.
    :TODO add this to the gene class?
    """
    skipped_exons_out = []
    for key1, key2 in pairwise(transcript_dict.keys()):
        if (len(transcript_dict[key1]) >= 1) and\
                (len(transcript_dict[key2]) >= 1):
            _, skipped_exons = compare_two_transcripts( key1, key2, 
                    transcript_dict)
            if len(skipped_exons) >=1:
                skipped_exons_out.append(skipped_exons)
        else: pass
    return(skipped_exons_out)


def generate_to_plot_tuple(de, transcript_dict):
    """
    """
    if de.exon_num[0]:
        sea = 0
    else:
        sea = 1
    eoi = [de.exon_num[sea]]
    cigar_skipped = getattr(de, 'cigar{0!s}'.format(sea*1 + 1))
    if len(cigar_skipped) > 3:
        eoi.append(eoi[0] + 1)
    else: pass
    cpath = transcript_dict[de.tid[sea]]
    eoi = [i[1] for i in cigar_skipped if i[0] == 3]
    eoi2 = getattr(de,'cigar{0!s}'.format(2 - 1*sea))[0][1]
    # Move generation of to plot into diffevents?
    to_plot1 = [i for i in cpath if (i[2] >= min(eoi) - 1) and (i[2] <= max(eoi)+ 1)]
    transcript_dict[de.tid[sea]] = to_plot1
    #to_plot2 = [i for i in transcript_dict[de.tid[1-sea]]]
    to_plot2 = [i for i in transcript_dict[de.tid[1-sea]] if i[2] in
            [de.exon2[0], de.exon2[1]]]
    transcript_dict[de.tid[1-sea]] = to_plot2
    return(to_plot1, to_plot2, eoi, eoi2)

