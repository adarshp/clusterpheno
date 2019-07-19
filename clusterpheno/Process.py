import re, os
import subprocess as sp
import shutil as sh
from helpers import *

class Process(object):
    """ A template for a particle collision process."""
    def __init__(
            self, name, model, decay_channel,
            mg5_generation_syntax, energy, index):

        """ Initialize a new instance of Process with the following parameters:

        Parameters
        ----------
        name : str
            The name of the process, e.g. 'A_HZ', 'tt', etc.
        model : str
            The name of the model for MadGraph to import while generating the
            process. For example - '2HDM_HEFT', 'sm', etc.
        decay_channel : str
            The name of the decay channel. For example, 'bbll', 'fully_leptonic',
            etc.
        mg5_generation_syntax : str
            The generation syntax for this process (not including the model
            declaration). Example: ``generate p p > t t~``.
        energy : str
            The center-of-mass collision energy, in TeV.
        """
        self.name = name
        self.model = model
        self.decay_channel = decay_channel
        self.mg5_generation_syntax = mg5_generation_syntax
        self.energy = str(energy)+'_TeV'
        self.index = str(index)

        self.common_path = '/'.join([self.process_type()+'s', self.name,
                                     self.decay_channel, self.energy, self.index])
        self.directory = '/'.join(['Events', self.common_path])

    def create_directory(self, relative_mg5_path):
        """ Create a MadGraph5 directory for the process. """
        proc_card = '/'.join(['Cards/proc_cards', self.common_path+ '_proc_card.dat'])
        if not os.path.exists(os.path.dirname(proc_card)):
            try:
                os.makedirs(os.path.dirname(proc_card))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(proc_card, 'w') as f:
            f.write('import model {}\n'.format(self.model))
            f.write(self.mg5_generation_syntax+'\n')
            f.write('output '+self.directory)
        sp.call(['python',relative_mg5_path+'/bin/mg5_aMC', proc_card], stdout = open(os.devnull, 'w'))

    def process_type(self):
        if self.model == 'sm': return 'Background'
        else: return 'Signal'

    def copy_cards(self, run_card, pythia_card, delphes_card):
        """ Copy the run, pythia, and delphes cards to the process directory."""
        destination = self.directory+'/Cards/'
        sh.copy(run_card, destination+'run_card.dat')
        sh.copy(pythia_card, destination+'pythia_card.dat')
        sh.copy(delphes_card, destination+'delphes_card.dat')

    def generate_events_locally(self, nruns = 1, nevents = 10000):
        """ Generate events on your local computer.

        Parameters
        ----------

        nruns : int
            Number of runs to perform.
        nevents : int
            Number of events to generate per run.
        """

        self.setup_for_generation(nruns, nevents)
        with cd(self.directory):
            for run in range(0, nruns):
                sp.call(['./bin/generate_events','--laststep=delphes', '-f'])
                sp.call(['./bin/madevent','remove','all', 'parton', '-f'])
                sp.call(['./bin/madevent','remove','all', 'pythia', '-f'])
                # sp.call('rm -rf Events/run_*/tag_*_delphes_events.root', shell = True)

    def generate_events(self):
        """ Generate events on cluster."""
        with cd(self.directory):
            sp.call(['qsub', 'generate_events.pbs'], stdout = open(os.devnull, 'w'))

    def write_pbs_script(self, parser, nruns):
        with open(parser.get('PBS Templates', 'generate_script'), 'r') as f:
            string = f.read()
        with open(self.directory+'/generate_events.pbs', 'w') as f:
            f.write(string.format(jobname = self.name,
                                  username = parser.get('Cluster', 'username'),
                                  email = parser.get('Cluster', 'email'),
                                  group_list = parser.get('Cluster', 'group_list'),
                                  nruns = str(nruns),
                                  cput = str(30*nruns),
                                  walltime = str(60*nruns),
                                  cwd = os.getcwd(),
                                  mg5_process_dir = self.directory))
    def make_feature_array(self):
        with cd(self.directory+'/MakeFeatureArray/Build'):
            devnull = open(os.devnull, 'w')
            sp.call('./analyze.sh', shell = True,
                    stdout = devnull)
