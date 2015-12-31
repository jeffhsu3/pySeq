from itertools import tee, izip
# Requires bx python
from bx.intervals.intersection import Intersecter, Interval



def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return(izip(a,b))


class Exon(object):
    """ A region
    """

    def __init__(self, region, start, end):
        self.region = region
        try:
            self.start = int(start)
            self.end = int(end)
        except ValueError:
            print("Start and End positions need to be integers")



class Transcript(object):
    """ A collection of exons
    """


    def __init__(self, exons=[]):
       self.exons = exons




class Gene(object):
    """ A collection of transcripts
    """

    def __init__(self, transcripts=[]):
        self.transcripts = []

    def _unique_junctions(self):
        pass

    def hmm(self):
        pass



def break_exons(exon1, exon2):
    """ Returns a list of new exons

    Breaks a interval into 2 intervals if it overlaps, upstream exon always
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
    """ Returns a list of sets
    Calculates the unique regions defined such that only the same elements
    are bound to it.
    """

    # Since most exons are shared, remove the most common elements first
    common_set = reduce( lambda x, y: x & y, list_of_sets)
    rs = [i - common_set for i in list_of_sets]
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





def compare_two_transcripts(trans1, trans2, transcript_dict):
    """
    Returns the splice differences between two transcripts.
    Note this ignores TSS and just looks for splice junctions

    Parameters
    ----------
    trans1 - string of transcript of interest
    trans2 - string of second transcript of interest
    transcript_dict - a dictionary of transcript names with 
    values being a list of exons

    Returns:
    5' upstream exons - 
    3' downstram exons - 
    """
    t1 = transcript_dict[trans1]
    t2 = transcript_dict[trans2]
    tree = Intersecter()
    starts1 = [i[0] for i in t1]
    starts2 = [i[0] for i in t2]
    reverse = False
    if min(starts1) >= min(starts2):
        s1 = t2 
        s2 = t1
        reverse = True
    else:
        s1 = t1
        s2 = t2
    if reverse:
        torder = (trans2, trans1)
    else:
        torder = (trans1, trans2)

    for i in s1:
        tree.add_interval(Interval(int(i[0]), int(i[1]), 
            value={'anno':i[2]}))
    matching_exons = []
    exclusive_juncs = []
    skipped_exons = []
    # Perform the query
    start_of_exons = None
    s1.sort(key=lambda x: x[2])
    s2.sort(key=lambda x: x[2])
    max_exon_1 = max([i[2] for i in s1])
    max_exon_2 = max([i[2] for i in s2])
    for start, end, exon_n in s2:
        start = int(start)
        end = int(end)
        overlap = tree.find(int(start), int(end))
        if len(overlap) == 0:
            if start_of_exons:
                skipped_exons.append((start, end, 
                    (None, exon_n), (0,end-start)))
            else: pass
        elif len(overlap) == 1:
            if start_of_exons: pass
            else: start_of_exons = overlap[0].value['anno']
            if start == overlap[0].start and end == overlap[0].end:
                matching_exons.append((start, end, (overlap[0].value['anno'], 
                    exon_n), (0, 0)))
            else:
                sstart = min(start, overlap[0].start)
                ssend = max(end, overlap[0].end)
                # Ignore 5' or 3' differences
                if (exon_n == max_exon_2 and
                        overlap[0].value['anno'] == max_exon_1):
                    pass
                else:
                    exclusive_juncs.append(
                            (sstart, ssend,
                            (overlap[0].value['anno'], exon_n), 
                            (overlap[0].start - start, overlap[0].end - end) 
                            )
                    )
        else:
            if start_of_exons:
                pass
            else: start_of_exons = overlap[0].value['anno']
    # Checking for skipped exons of t1 missing in t2
    hit_exon = [i[2][0] for i in exclusive_juncs] 
    hit_exon.extend([i[2][0] for i in matching_exons])
    for start, end, exon_n in s1:
        if exon_n <= start_of_exons:
            pass
        elif exon_n in hit_exon:
            pass
        else:
            skipped_exons.append((start, end, (exon_n, None), (end-start)) ) 
    return(exclusive_juncs, torder, matching_exons, skipped_exons)


def pairwise_transcript_comparison(transcript_dict):
    """
    """
    skipped_exons_out = []
    for key1, key2 in pairwise(transcript_dict.keys()):
        exclusive_juncs, to, me, skipped_exons = compare_two_transcripts(
                key1, key2, transcript_dict)
        if len(skipped_exons) >=1:
            skipped_exons_out.append((key1, key2))
    return(skipped_exons_out)

