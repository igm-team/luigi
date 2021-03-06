# -*- coding: utf-8 -*-
#
# Copyright 2012-2015 Spotify AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
The SunGrid Engine runner

The main() function of this module will be executed on the
compute node by the submitted job. It accepts as a single
argument the shared temp folder containing the package archive
and pickled task to run, and carries out these steps:

- extract tarfile of package dependencies and place on the path
- unpickle SGETask instance created on the master node
- run SGETask.work()

On completion, SGETask on the master node will detect that
the job has left the queue, delete the temporary folder, and
return from SGETask.run()
"""

import os
import sys
from pprint import pprint as pp
try:
    import cPickle as pickle
except ImportError:
    import pickle
import logging
import tarfile
from time import time, ctime


def _do_work_on_compute_node(
    work_dir, random_id, tarball=False, start_time=None, debug=False):

    cwd = os.getcwd()
    if tarball:
        # Extract the necessary dependencies
        _extract_packages_archive(work_dir)
    if debug:
        sys.stderr.write("extracted tar after {} seconds\n".format(
            time() - start_time))

    # Open up the pickle file with the work to be done
    os.chdir(work_dir)
    with open("{random_id}.job-instance.pickle".format(
        random_id=random_id), "r") as f:
        job = pickle.load(f)
    if debug:
        sys.stderr.write("loaded pickled data after {} seconds\n".format(
            time() - start_time))

    # Do the work contained
    os.chdir(cwd)
    job.work()


def _extract_packages_archive(work_dir):
    package_file = os.path.join(work_dir, "packages.tar")
    if not os.path.exists(package_file):
        return

    curdir = os.path.abspath(os.curdir)

    os.chdir(work_dir)
    tar = tarfile.open(package_file)
    for tarinfo in tar:
        tar.extract(tarinfo)
    tar.close()
    if '' not in sys.path:
        sys.path.insert(0, '')

    os.chdir(curdir)

def rnr_log(args):
    y='0'
    if "JOB_ID" in os.environ:
        y=os.environ['JOB_ID']
    outs = '%08.2d' % (int(y)) # just don't care...
    x='/nfs/seqscratch09/dsth/luigi/'
    for i in range(0,len(outs)):
        if i%2==0:
            x=x+outs[i]
        else:
            x=x+outs[i]+'/'
    if not os.path.isdir(x):
        os.makedirs(x)
    x=x+'rnr.txt'
    with open(x,'w') as fh:
        fh.write('hostname= '+os.environ['HOSTNAME']+'\n')
        fh.write('args= '+str(args)+'\n')
        fh.write('env= '+str(os.environ))
    # print("using "+x)

def main(args=sys.argv):
    """Run the work() method from the class instance in the file "job-instance.pickle".
    """

    # rnr_log(args)

    try:
        debug = "--debug" in args
        if debug:
            start_time = time()
            sys.stderr.write("starting at {}\n".format(ctime()))
        else:
            start_time = None
        tarball = "--tarball" in args
        # Set up logging.
        logging.basicConfig(level=logging.WARN)
        work_dir = args[1]
        assert os.path.exists(work_dir), "First argument to sge_runner.py must be a directory that exists"
        project_dir = args[2]
        sys.path.append(project_dir)
        random_id = args[3]
        _do_work_on_compute_node(work_dir, random_id, tarball, start_time, debug)
    except Exception as e:
        # Dump encoded data that we will try to fetch using mechanize
        print(e)
        raise

if __name__ == '__main__':
    main()
   
