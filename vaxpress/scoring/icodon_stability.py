#
# VaxPress
#
# Copyright 2023 Hyeshik Chang
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# “Software”), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
# THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from . import ScoringFunction

ICODON_SPECIES_MAPPING = {
    'Homo sapiens': 'human',
    'Mus musculus': 'mouse',
    'Danio rerio': 'zebrafish',
}

class iCodonStabilityFitness(ScoringFunction):

    iCodon_initialized = False
    single_submission = False
    predfuncs = {} # cache for iCodon predict_stability functions

    name = 'iCodon'
    requires = ['species']

    def __init__(self, weight, species, length_cds):
        self.weight = weight
        if species not in ICODON_SPECIES_MAPPING:
            raise ValueError(f"Unsupported species by iCodon: {species}")
        self.species = ICODON_SPECIES_MAPPING[species]
        self.length_cds = length_cds

    def __call__(self, seqs):
        if not self.iCodon_initialized:
            import os
            os.environ['TZ'] = 'UTC' # dplyr requires this to run in singularity

            import rpy2.robjects.packages as rpackages
            rpackages.importr('iCodon')
            rpackages.importr('stringr')

            import rpy2.robjects as ro
            ro.r['options'](warn=-1)

            self.iCodon_initialized = True

        import rpy2.robjects as ro
        if self.species not in self.predfuncs:
            self.predfuncs[self.species] = ro.r['predict_stability'](self.species)

        # Remove duplicates since iCodon refuses prediction of sequence lists
        # containing duplicates
        query = list(set(seqs))
        results = self.predfuncs[self.species](seqs)
        results = dict(zip(query, results))

        pred = [float(results[s]) for s in seqs]
        scores = [s * self.weight for s in pred]
        return {'pred_stability': scores}, {'pred_stability': pred}
