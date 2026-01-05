# cumolfind - CUDA Accelerated Molecule Finder

Purpose: This package is designed to analyze extensive trajectory data and identify specific molecules of interest within that trajectory.

This package requires TorchANI as an external submodule; to install, run

```bash
git clone --recurse-submodules git@github.com:roitberg-group/cumolfind.git
```

## Key Features

- Users can define the molecules of interest in a custom database.
- The program searches for these molecules in each frame of the trajectory. This is done by initially fragmenting the data to identify subgraphs, and then determining if these subgraphs match any molecules in the user's database.
- The identified molecule information is saved in a dataframe for easy post-analysis.

## Environment Setup on Blackwell GPUs (CUDA 12.9.1)

Before installing, be sure you have a compatible CUDA version.
On the HiPerGator supercomputer, you can run:

```bash
srun --partition=hpg-b200 --gpus=1 --time=1:00:00 --mem=8gb --pty bash -i
module load cuda/12.9.1
```

Then, to install, run

```bash
mamba env create -f environment.yaml  # NOTE: Edit first line to rename environment as you wish
mamba activate ENV_NAME

cd external/torchani
pip install --no-deps -v -e .
ani build-extensions

mamba install -c rapidsai -c conda-forge -c nvidia cudf=25.02 cugraph=25.02 cuda-version=12.9 mdtraj

cd /path/to/cumolfind

pip install -e .
```

NOTE: Some of these steps might seem excessive, but conda/mamba solvers have issues installing all required dependencies simultaneously.

## Usage

`cumolfind` provides several command-line tools:

**Generating Molecule Database:**

```bash
cd data
python pubchem.py
```

This utility builds a molecule database using the PubChemPy library. The database includes columns such as "graph, formula, smiles, name, flatten_formula".

**Finding Molecules in Trajectory:**

```bash
cumolfind-molfind --help

Analyze trajectory

positional arguments:
  traj_file             Trajectory file to be analyzed
  top_file              Topology file to be analyzed
  mol_pq                Molecule database file

options:
  -h, --help            show this help message and exit
  --time_offset TIME_OFFSET
                        Time offset for the trajectory
  --dump_interval DUMP_INTERVAL
                        How many timesteps between frame dumps
  --timestep TIMESTEP   Timestep used in the simulation (fs)
  --output_dir OUTPUT_DIR
                        Output directory
  --num_segments NUM_SEGMENTS
                        Number of segments to divide the trajectory into
  --segment_index SEGMENT_INDEX
                        Index of the segment to analyze
```

Example

```bash
cumolfind-molfind ~/trajectory.dcd ~/topology.pdb ./data/molecule_data.pq --dump_interval=50 --timestep=0.25 --output_dir=test_analyze1 --num_segments=10 --segment_index=2
```

Use this command to analyze trajectory files and find molecules. It exports two files:

- `{traj_file}_formula.pq`: Database with "frame, local_frame, formula, count, time".
- `{traj_file}_molecule.pq`: Database with "frame, local_frame, hash, formula, smiles, name, atom_indices, time".

**Splitting Trajectory:**

```bash
cumolfind-split_traj --traj_file [path/to/traj_file] [other arguments]
```

This command splits a large trajectory file into smaller segments, naming each segment with the suffix `traj_name_x.xns.dcd`, where `x.x` represents the time offset for the start of each segment.

**Submit analysis job parallaly:**

```bash
python /blue/roitberg/apps/lammps-ani/cumolfind/submit_analysis.py --help
usage: submit_analysis.py [-h] --traj TRAJ --top TOP --num_segments NUM_SEGMENTS --mol_pq MOL_PQ [--output_dir OUTPUT_DIR] [-y]

Parallelize cumolfind analysis.

optional arguments:
  -h, --help            show this help message and exit
  --traj TRAJ           Directory containing trajectory files or a single trajectory file.
  --top TOP             Topology file.
  --num_segments NUM_SEGMENTS
                        Number of segments for each trajectory.
  --mol_pq MOL_PQ       Molecule database file
  --output_dir OUTPUT_DIR
                        Output directory
  -y                    If provided, the job will be submitted. If not, the job will only be prepared but not submitted.
```

Example

```bash
python ./submit_analysis.py --traj=~/testrun/ --top=~/toplogy.pdb --num_segments=2 --mol_pq=./data/molecule_data.pq
```
