from random import shuffle, seed
from multiprocessing import Process, Pool
from shutil import copyfile, rmtree
from tqdm import tqdm
import math
import os, sys, argparse
import inspect
import json

try:
    import numpy as np
except:
    print "Failed to import numpy package."
    sys.exit(-1)
try:
    from plyfile import PlyData, PlyElement
except:
    print "Please install the module 'plyfile' for PLY i/o, e.g."
    print "pip install plyfile"
    sys.exit(-1)

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import util
import util_3d

parser = argparse.ArgumentParser()
parser.add_argument('--pred_path', required=True, help='path to predicted labels files as .txt evaluation format')
parser.add_argument('--scan_path', required=True, help='path to the *_vh_clean_2.ply parent directory (scans directory)')
parser.add_argument('--output_path', required=True, help='directory for output .ply files')
parser.add_argument('--pred_format', required=False, default='txt', help='in which format predictions are stored txt or npy')
parser.add_argument('--num_vis', required=False, default=15, help='number of meshes to visualize (default: 10)')
parser.add_argument('--seed', required=False, default=139, help='random seed for shuffling available predictions (default: 139)')
opt = parser.parse_args()


def visualize(pred_file, scan_path, output_file):
    if not output_file.endswith('.ply'):
        util.print_error('output file must be a .ply file')
    colors = util.create_color_palette()
    num_colors = len(colors)
    if opt.pred_format == "txt":
        ids = util_3d.load_ids(pred_file)
    else:
        ids = np.load(pred_file)
    with open(scan_path, 'rb') as f:
        plydata = PlyData.read(f)
        num_verts = plydata['vertex'].count
        if num_verts != len(ids):
            util.print_error('#predicted labels = ' + str(len(ids)) + 'vs #mesh vertices = ' + str(num_verts))
        # *_vh_clean_2.ply has colors already
        for i in range(num_verts):
            if ids[i] >= num_colors:
                util.print_error('found predicted label ' + str(ids[i]) + ' not in nyu40 label set')
            color = colors[ids[i]]
            plydata['vertex']['red'][i] = color[0]
            plydata['vertex']['green'][i] = color[1]
            plydata['vertex']['blue'][i] = color[2]
    plydata.write(output_file)

def visualize_unpack(args):
    return visualize(*args)

if __name__ == "__main__":
    N = opt.num_vis
    pred_files = [f for f in os.listdir(opt.pred_path) if f.endswith('.{}'.format(opt.pred_format)) and f != 'semantic_instance_evaluation.txt']
    pred_files.sort()
    seed(opt.seed)
    shuffle(pred_files)

    if not os.path.exists(opt.output_path):
        os.mkdir(opt.output_path)

    pool = Pool(processes=10)
    pool_args = []
    print("=== Start arguments collection and ground truth copy")
    for fname in tqdm(pred_files[:N]):
        scene = fname.split(".")[0]
        pred_file = os.path.join(opt.pred_path, "{0}.{1}".format(scene, opt.pred_format))
        scan_path = os.path.join(opt.scan_path, "{0}/{0}_vh_clean_2.ply".format(scene))
        output_file = os.path.join(opt.output_path, "{0}_semantics_pr.ply".format(scene))

        pool_args.append((pred_file, scan_path, output_file, ))
        copyfile(os.path.join(opt.scan_path, "{0}/{0}_vh_clean_2.labels.ply".format(scene)), os.path.join(opt.output_path, "{0}_semantics_gt.ply".format(scene)))

    print("=== Start multiprocessing pool")
    # result = pool.map(visualize_unpack, pool_args)
    r = list(tqdm(pool.imap(visualize_unpack, pool_args), total=len(pool_args)))