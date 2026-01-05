import torch

import argparse
import os
from pathlib import Path
import warnings
import torch
import pandas as pd
from pathlib import Path
from .top_loader import load_topology
from .analyze_traj import analyze_all_frames


def _init_rmm(pool_max_gb: int = 450, use_managed: bool = True) -> bool:
    """Initialize RMM pool allocator safely after confirming GPU availability.

    Returns True if RMM was initialized and set as the current allocator, else False.
    """
    try:
        if not torch.cuda.is_available() or torch.cuda.device_count() == 0:
            print(
                "[molfind] CUDA not available or no devices visible; skipping RMM initialization.")
            return False

        # Touch the CUDA context early to surface device errors now
        _ = torch.cuda.current_device()

        import rmm.mr as mr
        from rmm.allocators.torch import rmm_torch_allocator

        base = mr.ManagedMemoryResource() if use_managed else mr.CudaMemoryResource()
        pool = mr.PoolMemoryResource(
            base,
            maximum_pool_size=pool_max_gb * 1024**3,
        )
        mr.set_current_device_resource(pool)

        # Configure PyTorch to use RAPIDS Memory Manager (RMM)
        torch.cuda.memory.change_current_allocator(rmm_torch_allocator)
        print(
            f"[molfind] RMM pool initialized (managed={use_managed}, max={pool_max_gb}GB)")
        return True
    except Exception as e:
        # Do not fail hard here; the rest of the pipeline can still run
        print(f"[molfind] RMM initialization skipped due to error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Trajectory analysis")

    parser.add_argument("traj_file", type=str,
                        help="Trajectory file to be analyzed")
    parser.add_argument("top_file", type=str,
                        help="H5 topology file to be analyzed")
    parser.add_argument("mol_pq", type=str, help="Molecule database file")
    parser.add_argument("--time_offset", type=float,
                        help="Time offset for the trajectory", default=0.0)
    parser.add_argument(
        "--dump_interval", type=int, help="How many timesteps between frame dumps", default=50
    )
    parser.add_argument("--timestep", type=float,
                        help="Timestep used in the simulation (fs)", default=0.25)
    parser.add_argument("--output_dir", type=str,
                        help="Output directory", default="analyze")
    parser.add_argument(
        "--num_segments", type=int, default=1, help="Number of segments to divide the trajectory into"
    )
    parser.add_argument("--segment_index", type=int, default=0,
                        help="Index of the segment to analyze")

    args, remaining_args = parser.parse_known_args()

    args = parser.parse_args()

    # Initialize GPU memory management after arguments are parsed
    _init_rmm()

    print("Analyzing trajectory...")
    if Path(args.traj_file).suffix == ".xyz":
        warnings.warn(
            "XYZ file does not have PBC information, please use DCD/NetCDF/LAMMPSTRJ file instead")

    output_directory = args.output_dir
    os.makedirs(output_directory, exist_ok=True)

    topology = load_topology(args.top_file)
    # time_analyze0 = time.time()
    # this will time the first frame too, so putting timer inside the function
    # Analyze the entire trajectory
    analyze_all_frames(
        topology,
        args.traj_file,
        args.time_offset,
        args.dump_interval,
        args.timestep,
        output_directory,
        args.mol_pq,
        args.num_segments,
        args.segment_index,
    )
    # print("Analyzed trajectory in", time.time() - time_analyze0, "seconds")


if __name__ == "__main__":
    main()
