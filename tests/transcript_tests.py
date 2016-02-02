import unittest
import pysam
from genda.transcripts import (Exon, Gene, Transcript, unique_sets,
        compare_two_transcripts)

class TestGeneBreaks(unittest.TestCase):

    def setUp(self):
        self.simple_gene = Gene([Transcript([Exon('chr1', 10, 20),
                                             Exon('chr1', 50, 60),
                                             Exon('chr1', 80, 120)]),
                                 Transcript([Exon('chr1', 10, 20),
                                             Exon('chr1', 80, 120)]),
                                 Transcript([Exon('chr1', 5, 20),
                                             Exon('chr1', 50, 60),
                                             Exon('chr1', 80,120)])])
        self.seperate_genes = 0

        self.read_length = 75

    def uniqueSets(self):
        """ Test to calculate the unique regions such that, given an
        annotation, regions are unique iff a set of s.  Note,
        regions defined in such a manner can be disjoint.

        """
        pass






class TestGenerateSets(unittest.TestCase):

    def setUp(self):
        self.set_a = set(['a', 'b', 'c'])
        self.set_b = set(['a', 'b'])
        self.set_c = set(['a', 'b', 'd'])


    def find_sets(self):
        self.assertEqual(unique_sets([self.set_a, self.set_b, self.set_c]),
                                     [set(['a', 'b']), set(['c']), set(['d'])])



class TestCompareTwoTranscripts(unittest.TestCase):
    """:TODO add more test cases.  Bad implementation
    if I have to test so many edgecases
    """
    def setUp(self):
        self.skipped_exon = (50, 60)
        self.transcript_dict = {
                't1' : [
                    (10, 20, 1), 
                    (50, 60, 2), #Skipped exon 
                    (70, 90, 3),
                    (120, 180, 4),],
                't2' : [(12, 20, 1), 
                    (70, 90, 2)],
                'no_overlap' : 
                [(200,210, 1),
                 (240, 260, 2)]
                }
        
        self.tdict2 = {'t1' : 
                [(12, 20, 1), 
                 (50, 60, 2), 
                 (70, 90, 3),],
                't2' : 
                [(10, 20, 1), 
                 (70, 90, 2)],

                }

        self.tnegative = {
                }
        self.doubleskip = {'full':
                [(12, 20, 1),
                 (30, 40, 2),
                 (50, 60, 3),
                 (70, 80, 4)],
                'skipped':
                [(5, 20, 1),
                 (70, 80, 2)]}
        self.diffmatch = None

    def test_compare_transcripts_skipped_exon_simple(self):
        exclusive_juncs, torder, matching_exons, skipped_exons =\
                compare_two_transcripts('t1', 't2', self.transcript_dict)
        se = skipped_exons[0]
        self.assertEqual(len(skipped_exons), 1)
        self.assertEqual(se.transcript_ids, ('t1', 't2'))
        self.assertEqual([(3, 30), (0, 10), (3, 10)], se.cigar2)
        self.assertEqual((50, 60), (se.start, se.end))
        self.assertEqual('skipped_exon', se.event_type)
        self.assertEqual((2, None), se.exon_num)
        self.assertEqual((1, 2), se.exon2)

    def test_no_overlap_compare_transcripts(self):
        exclusive_juncs, torder, matching_exons, skipped_exons =\
                compare_two_transcripts('t1', 'no_overlap', self.transcript_dict)
        self.assertEqual(len(skipped_exons), 0)

    def test_s2_has_skipped_exon(self):
        exclusive_juncs, torder, matching_exons, skipped_exons =\
                compare_two_transcripts('t1', 't2', self.tdict2)
        self.assertEqual(len(skipped_exons), 1)
        se = skipped_exons[0]
        self.assertEqual(se.transcript_ids, ('t2', 't1'))
        self.assertEqual(skipped_exons[0].cigar1,  [(3, 50)])
        self.assertEqual(skipped_exons[0].cigar2,  [(3, 30), (0, 10), (3, 10)]) 
        self.assertEqual((1,2), se.exon2)


    def test_two_skipped_exons(self):
        exclusive_juncs, torder, matching_exons, skipped_exons =\
                compare_two_transcripts('full', 'skipped', self.doubleskip)
        se = skipped_exons[0]
        self.assertEqual(se.cigar1, [(3, 50)])
        

        


if __name__ == '__main__':
    unittest.main()