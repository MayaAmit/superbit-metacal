import os
import sys
from glob import glob
from astropy.table import Table
import matplotlib.pyplot as plt
import utils
import pudb

class Diagnostics(object):
    def __init__(self, name, config):
        self.name = name
        self.config = config

        # plotdir is the directory where all pipeline plots are saved
        # plot_outdir is the output plot directory for *this* diagnostic type
        self.plotdir = None
        self.plot_outdir = None

        # outdir is the location of module outputs
        if 'outdir' in config:
            self.outdir = config['outdir']
        else:
            # Will be set using run_options
            self.outdir = None

        return

    def run(self, run_options, logprint):
        logprint(f'Running diagnostics for {self.name}')

        # If outdir wasn't set in init, do it now
        if self.outdir is None:
            try:
                self.outdir = run_options['outdir']
            except KeyError as e:
                logprint('ERROR: Outdir must be set in either module ' +\
                         'config or run_options!')
                raise e

        self._setup_plot_dirs()

        return

    def _setup_plot_dirs(self):
        '''
        Must be run after self.outdir is set
        '''

        assert(hasattr(self, 'outdir'))

        self.plotdir = os.path.join(self.outdir, 'plots')
        self.plot_outdir = os.path.join(self.plotdir, self.name)

        for p in [self.plotdir, self.plot_outdir]:
            utils.make_dir(p)

        return

class TruthDiagnostics(Diagnostics):
    '''
    Some modules have a corresponding truth catalog
    to compare to
    '''

    def __init__(self, name, config):
        super(TruthDiagnostics, self).__init__(name, config)

        self.truth = None

        return

    def run(self, run_options, logprint):
        super(TruthDiagnostics, self).run(run_options, logprint)

        self._setup_truth_cat()

        return

    def _setup_truth_cat(self):
        '''
        Some diagnostics will require a truth catalog

        Assumes the truth cat is in self.outdir, which
        must be set beforehand
        '''

        assert(hasattr(self, 'outdir'))

        truth_files = glob(os.path.join(self.outdir, '*truth*.fits'))

        # After update, there should only be one
        N = len(truth_files)
        if N != 1:
            raise Exception(f'There should only be 1 truth table, not {N}!')

        truth_file = truth_files[0]

        self.truth = Table.read(truth_file)

        return

class GalSimDiagnostics(TruthDiagnostics):

    def __init__(self, name, config):
        super(GalSimDiagnostics, self).__init__(name, config)

        # ...

        return

    def run(self, run_options, logprint):

        super(GalSimDiagnostics, self).run(run_options, logprint)

        ## Check consistency of truth tables
        self.plot_compare_truths(run_options, logprint)

        return

    def plot_compare_truths(self, run_options, logprint):
        '''
        NOTE: No longer relevant, we have updated code
        to produce only one truth cat

        That is why this function does not use self.truth
        '''

        # Not obvious to me why there are multiple tables - this here
        # just to prove this.

        logprint('Diagnostic: Comparing truth catalogs...')

        truth_tables = glob(os.path.join(self.outdir, 'truth*.fits'))
        N = len(truth_tables)

        tables = []
        for fname in truth_tables:
            tables.append(Table.read(fname))

        cols = ['ra', 'flux', 'hlr']
        Nrows = len(cols)
        Nbins = 30
        ec = 'k'
        alpha = 0.75

        for i in range(1, Nrows+1):
            plt.subplot(Nrows, 1, i)

            col = cols[i-1]

            k = 1
            for t in tables:
                plt.hist(t[col], bins=Nbins, ec=ec, alpha=alpha, label=f'Truth_{k}')
                k += 1

            plt.xlabel(f'True {col}')
            plt.ylabel('Counts')
            plt.legend()

            if ('flux' in col) or ('hlr' in col):
                plt.yscale('log')

        plt.gcf().set_size_inches(9, 3*Nrows+2)

        outfile = os.path.join(self.plotdir, 'compare_truth_tables.pdf')
        plt.savefig(outfile, bbox_inches='tight')

        return

class MedsmakerDiagnostics(Diagnostics):
    pass

class MetacalDiagnostics(TruthDiagnostics):

    def __init__(self, name, config):
        super(MetaCalDiagnostics, self).__init__(name, config)

        # ...

        return

    def run(run_options, logprint):
        super(MetacalDiagnostics, self).run(run_options, logprint)

        self.plot_compare_mags(run_options, logprint)

        return

    def plot_compare_mags(run_options, logprint):
        pass

class NgmixFitDiagnostics(TruthDiagnostics):

    def __init__(self, name, config):
        super(NgmixFitDiagnositcs, self).__init__(name, config)

        return

    def run(run_options, logprint):
        super(NgmixFitDiagnostics, self).run(run_options, logprint)

        # outdir is now guaranteed to be set
        # self.ngmix_config_file =

        self.compare_to_truth(run_options, logprint)

        return

    def compare_to_truth(run_options, logprint):
        '''
        Plot meas vs. true for a variety of quantities
        '''

        self.plot_pars_compare(run_options, logprint)

        return

    def plot_pars_compare(run_options, logprint):
        logprint('Comparing meas vs. true ngmix pars')

        # gal_model = ngmix_config[]
        # true_pars = self.truth['']

        return

class ShearProfileDiagnostics(Diagnostics):
    pass

def get_diagnostics_types():
    return DIAGNOSTICS_TYPES

# NOTE: This is where you must register a new diagnostics type
DIAGNOSTICS_TYPES = {
    'galsim': GalSimDiagnostics,
    'medsmaker': MedsmakerDiagnostics,
    'Metacal': MetacalDiagnostics,
    'ShearProfile': ShearProfileDiagnostics,
}

def build_diagnostics(name, config):
    name = name.lower()

    if name in DIAGNOSTICS_TYPES.keys():
        # User-defined input construction
        diagnostics = DIAGNOSTICS_TYPES[name](name, config)
    else:
        # Attempt generic input construction
        diagnostics = Diagnostics(name, config)

    return diagnostics