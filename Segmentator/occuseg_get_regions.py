import multiprocessing
from multiprocessing.pool import ThreadPool
import subprocess
import shlex
from tqdm import tqdm
import os, sys, argparse

parser = argparse.ArgumentParser()
parser.add_argument('--scans_path', required=True, help='')

opt = parser.parse_args()

if __name__ == "__main__":
    ply_paths = [os.path.join(opt.scans_path, f, f+"_vh_clean_2.ply") for f in os.listdir(opt.scans_path)]

    pool_args = ply_paths
    
    print("=== Start multiprocessing pool")
    
    def call_proc(cmd):
        """ This runs in a separate thread. """
        p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return (out, err)

    pbar = tqdm(total=len(pool_args))
    def update(*a):
        pbar.update()

    pool = ThreadPool(multiprocessing.cpu_count())
    results = []
    for arg in pool_args:
        results.append(pool.apply_async(call_proc, ("./segmentator {}".format(arg), ), callback=update))

    # Close the pool and wait for each running task to complete
    pool.close()
    pool.join()