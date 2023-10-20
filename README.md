# visualizer-abac-log

## Task to run visualizer
- generate abac data by running the following command the output will be saved in the same directory as the script with the name abac_res.txt
```
python3 generate_abac_data.py filename
```
- run the following command to generate the visualizer
```
python3 visualizer.py abac_datafile -l file1 file2 file3 ... filen
```
the program will open a window with the visualizer