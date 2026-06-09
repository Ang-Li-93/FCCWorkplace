# Combine (`run_combine.sh`)

The CMS `HiggsAnalysis-CombinedLimit` submodule has been removed in favour of the
FCCSW Singularity image. Use the wrapper:

```shell
./run_combine.sh combine -M MultiDimFit datacard.root
./run_combine.sh text2workspace.py datacard.txt
```

Override the image with `COMBINE_IMG=/path/to/other.sif` if needed.
