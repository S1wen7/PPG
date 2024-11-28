import sys
from pathlib import Path
import wfdb
import pandas as pd
from pprint import pprint

# Specify the name of the MIMIC-IV Waveform Database on PhysioNet
database_name = 'mimic4wdb/0.1.0'

## Get a list of records
# Each subject may be associated with multiple records
subjects = wfdb.get_record_list(database_name)
print(f"The '{database_name}' database contains data from {len(subjects)} subjects")

# Set max number of records to load
max_records_to_load = 200

# Iterate the subjects to get a list of records
records = []
for subject in subjects:
    studies = wfdb.get_record_list(f'{database_name}/{subject}')
    for study in studies:
        records.append(Path(f'{subject}{study}'))
        # stop if we've loaded enough records
        if len(records) >= max_records_to_load:
            print("Reached maximum required number of records.")
            break

print(f"Loaded {len(records)} records from the '{database_name}' database.")

## Look at the records
# Format and print first five records
first_five_records = [str(x) for x in records[0:5]]
first_five_records = "\n - ".join(first_five_records)
print(f"First five records: \n - {first_five_records}")

print("""
Note the formatting of these records:
 - intermediate directory ('p100' in this case)
 - subject identifier (e.g. 'p10014354')
 - record identifier (e.g. '81739927'
 """)

## Extract metadata for a record
# Specify the 4th record (note, in Python indexing begins at 0)
idx = 3
record = records[idx]
record_dir = f'{database_name}/{record.parent}'
print("PhysioNet directory specified for record: {}".format(record_dir))

# Specify the subject identifier
record_name = record.name
print("Record name: {}".format(record_name))

record_data = wfdb.rdheader(record_name, pn_dir=record_dir, rd_segments=True)
remote_url = f"https://physionet.org/content/{record_dir}/{record_name}.hea"
print(f"Done: metadata loaded for record '{record_name}' from the header file at:\n{remote_url}")

print(f"- Number of signals: {record_data.n_sig}".format())
print(f"- Duration: {record_data.sig_len/(record_data.fs*60*60):.1f} hours")
print(f"- Base sampling frequency: {record_data.fs} Hz")

segments = record_data.seg_name
print(f"The {len(segments)} segments from record {record_name} are:\n{segments}")

segment_metadata = wfdb.rdheader(record_name=segments[2], pn_dir=record_dir)

print(f"""Header metadata loaded for: 
- the segment '{segments[2]}'
- in record '{record_name}'
- for subject '{str(Path(record_dir).parent.parts[-1])}'
""")

print(f"This segment contains the following signals: {segment_metadata.sig_name}")
print(f"The signals are measured in units of: {segment_metadata.units}")

print(f"Earlier, we loaded {len(records)} records from the '{database_name}' database.")
required_sigs = ['ABP', 'Pleth']
# convert from minutes to seconds
req_seg_duration = 10*60

matching_recs = {'dir': [], 'seg_name': [], 'length': []}

for record in records:
    print('Record: {}'.format(record), end="", flush=True)
    record_dir = f'{database_name}/{record.parent}'
    record_name = record.name
    print(' (reading data)')
    record_data = wfdb.rdheader(record_name,
                                pn_dir=record_dir,
                                rd_segments=True)

    # Check whether the required signals are present in the record
    sigs_present = record_data.sig_name
    if not all(x in sigs_present for x in required_sigs):
        print('   (missing signals)')
        continue

    # Get the segments for the record
    segments = record_data.seg_name

    # Check to see if the segment is 10 min long
    # If not, move to the next one
    gen = (segment for segment in segments if segment != '~')
    for segment in gen:
        print(' - Segment: {}'.format(segment), end="", flush=True)
        segment_metadata = wfdb.rdheader(record_name=segment,
                                         pn_dir=record_dir)
        seg_length = segment_metadata.sig_len / (segment_metadata.fs)

        if seg_length < req_seg_duration:
            print(f' (too short at {seg_length / 60:.1f} mins)')
            continue

        # Next check that all required signals are present in the segment
        sigs_present = segment_metadata.sig_name

        if all(x in sigs_present for x in required_sigs):
            matching_recs['dir'].append(record_dir)
            matching_recs['seg_name'].append(segment)
            matching_recs['length'].append(seg_length)
            print(' (met requirements)')
            # Since we only need one segment per record break out of loop
            break
        else:
            print(' (long enough, but missing signal(s))')

print(f"A total of {len(matching_recs['dir'])} records met the requirements:")

# df_matching_recs = pd.DataFrame(data=matching_recs)
# df_matching_recs.to_csv('matching_records.csv', index=False)
# p=1