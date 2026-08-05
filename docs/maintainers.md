# Updating PandoraSpacraft Kernels

If you have to maintain this package you can use the `maintainence` module to update the CK and SPK files using telemetry, and update the test kernel if needed. You will need the quaternions from telemetry in their raw, unformated form as a CSV file, which look like this:

|    |        time |        q1 |         q2 |        q3 |       q4 |
|---:|------------:|----------:|-----------:|----------:|---------:|
|  0 | 1.76651e+12 |  0.435525 | -1.0177    | -0.95454  | 0.865711 |
|  1 | 1.7668e+12  | -1.02916  |  0.940569  |  0.157958 | 0.674988 |
|  2 | 1.76815e+12 | -0.203154 |  0.0986252 | -0.298318 | 0.927197 |
|  3 | 1.76815e+12 | -0.313266 |  0.126517  | -0.32174  | 0.883077 |
|  4 | 1.76815e+12 | -0.463277 |  0.159831  | -0.345662 | 0.798644 |

and the positions and velocities over time which look like this:

|    |        time |      p1 |      p2 |       p3 |      v1 |        v2 |      v3 |
|---:|------------:|--------:|--------:|---------:|--------:|----------:|--------:|
|  0 | 1.76815e+12 | 6544.48 | 1698.28 | -1759.2  | 2.08593 | -0.556566 | 7.23922 |
|  1 | 1.76815e+12 | 6556.82 | 1694.9  | -1715.72 | 2.03993 | -0.568475 | 7.25141 |
|  2 | 1.76815e+12 | 6576.84 | 1689.11 | -1643.1  | 1.9631  | -0.588273 | 7.27112 |
|  3 | 1.76815e+12 | 6596.09 | 1683.13 | -1570.3  | 1.88616 | -0.608106 | 7.2901  |
|  4 | 1.76815e+12 | 6614.57 | 1676.95 | -1497.31 | 1.80899 | -0.627867 | 7.30822 |

From a terminal or a notebook run the following to update CK and SPK. First build a CK and SPK from your full set of telemetry

```python
from pandoraspacecraft.maintenance import convert_telemetry_to_cks, convert_telemetry_to_spks
convert_telemetry_to_cks(quaternions_csv_filename)
convert_telemetry_to_spks(position_csv_filename)
```

You can then split these into each day using

```python
from pandoraspacecraft.maintenance import split_ck, split_spk
split_ck()
split_spk()
```

This will add the files to your package directory. You can then add and push these to GitHub. 

You can then restart your session and run the following to update the test data, if necessary. You would only do this if you changed the code base significantly or if you wanted to change the period of validity for the test data.

```python
from pandoraspacecraft.maintenance import make_test_data
make_test_data()
```

When you have finished your updates you should make sure to push them to the `pandoraspacecraft` repo. Inside the `utils.py` module update `ndays = X` to the number of weeks of CK and SPK files that should now be available.

These files are not included with the distribution of the package to pip and are instead downloaded and cached whenever you run the package. This ensures that the files are shared between multiple installs across different environments.