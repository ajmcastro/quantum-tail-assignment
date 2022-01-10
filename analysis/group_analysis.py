import sys, os
from os import walk
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
import argparse
import csv
import json
import pathlib

def read_file(path):
    analysis_path = ""
    for (dirpath, dirnames, filenames) in walk(path):
        if len(dirnames) == 0:
            files = []
            for filename in filenames:
                if filename.endswith(('json')) and filename != "analysis.json":
                    files.append(filename)
            if len(files) > 0:
                group_same_instance_data(files, dirpath)
                analysis_path = pathlib.Path(dirpath+"/"+files[0]).parent.parent.parent
    for (dirpath, dirnames, filenames) in walk(analysis_path):
        files = []
        if len(dirnames) == 0:
            for filename in filenames:
                if filename == "analysis.json":
                    files.append(dirpath+"/"+filename)
    

def group_flights_data(filenames, dirpath):
    final_data = {
        'num_aircraft': 0,
        'num_flights': 0,
        'num_teorico_var': 0,
        'energy': 0,
        'model_time': 0,
        'solving_time': 0,
        'num_variables' : 0,
        'fixed_variables' : 0,
        'aux_variables' : 0,
        'num_flights_aircraft_model' : {},
        'flight_minutes_aircraft_model' : {},
        'total_cost' : 0,
        'free_seats' : 0,
        'extra_flights' : 0,
        'not_assigned_flights' : 0, 
    }
    for filee in filenames:
        with open(filee) as f:
            data = json.load(f)
            final_data['energy'] += data['energy']
            final_data['model_time'] += data['model_time_seconds']
            final_data['solving_time'] += data['solving_time_seconds']
            final_data['num_variables'] += data['num_variables']
            final_data['fixed_variables'] += data['fixed_variables']
            final_data['aux_variables'] += data['aux_variables']
            for model in data['num_flights_per_aircraft_model']:
                if model in final_data['num_flights_aircraft_model']:
                    final_data['num_flights_aircraft_model'][model] += data['num_flights_per_aircraft_model'][model]
                else:
                    final_data['num_flights_aircraft_model'].update({model: data['num_flights_per_aircraft_model'][model]})
            for model in data['flight_minutes_per_aircraft_model']:
                if model in final_data['flight_minutes_aircraft_model']:
                    final_data['flight_minutes_aircraft_model'][model] += data['flight_minutes_per_aircraft_model'][model]
                else:
                    final_data['flight_minutes_aircraft_model'].update({model: data['flight_minutes_per_aircraft_model'][model]})
            final_data['total_cost'] += data['total_cost']
            final_data['free_seats'] += data['free_seats']
            final_data['extra_flights'] += data['extra_flights']
            final_data['not_assigned_flights'] += data['not_assigned_flights']
    
    for data in final_data:
        if data == 'num_flights_aircraft_model' or data == 'flight_minutes_aircraft_model':
            for model in final_data[data]:
                final_data[data][model] /= len(filenames)
        else:
            final_data[data] /= len(filenames)
    final_data['num_aircraft'] = 
    final_data['num_flights'] = 
    final_data['num_teorico_var'] = 


def group_same_instance_data(filenames, dirpath):
    final_data = {
        'energy': 0,
        'model_time': 0,
        'solving_time': 0,
        'num_variables' : 0,
        'fixed_variables' : 0,
        'aux_variables' : 0,
        'num_flights_aircraft_model' : {},
        'flight_minutes_aircraft_model' : {},
        'total_cost' : 0,
        'free_seats' : 0,
        'extra_flights' : 0,
        'not_assigned_flights' : 0, 
    }
    for filee in filenames:
        print(filee)
        with open(dirpath+"/"+filee) as f:
            data = json.load(f)
            final_data['energy'] += data['energy']
            final_data['model_time'] += data['model_time_seconds']
            final_data['solving_time'] += data['solving_time_seconds']
            final_data['num_variables'] += data['num_variables']
            final_data['fixed_variables'] += data['fixed_variables']
            final_data['aux_variables'] += data['aux_variables']
            for model in data['num_flights_per_aircraft_model']:
                if model in final_data['num_flights_aircraft_model']:
                    final_data['num_flights_aircraft_model'][model] += data['num_flights_per_aircraft_model'][model]
                else:
                    final_data['num_flights_aircraft_model'].update({model: data['num_flights_per_aircraft_model'][model]})
            for model in data['flight_minutes_per_aircraft_model']:
                if model in final_data['flight_minutes_aircraft_model']:
                    final_data['flight_minutes_aircraft_model'][model] += data['flight_minutes_per_aircraft_model'][model]
                else:
                    final_data['flight_minutes_aircraft_model'].update({model: data['flight_minutes_per_aircraft_model'][model]})
            final_data['total_cost'] += data['total_cost']
            final_data['free_seats'] += data['free_seats']
            final_data['extra_flights'] += data['extra_flights']
            final_data['not_assigned_flights'] += data['not_assigned_flights']
    
    for data in final_data:
        if data == 'num_flights_aircraft_model' or data == 'flight_minutes_aircraft_model':
            for model in final_data[data]:
                final_data[data][model] /= len(filenames)
        else:
            final_data[data] /= len(filenames)

            
    print_analysis(dirpath, final_data)
    # return max(num_variables), sum(energy)/len(energy), sum(model_time)/len(model_time), sum(solution_time)/len(solution_time)

def print_analysis(dirpath, final_data):
    #row_list = {}
    # row_list.append(["Filename", "Num_BQM_Var", "Energy", "Model_Time(ms)", "Sol_Time(ms)"])
    # for i in range(len(filenames)):
    #     row = []
    #     row.append(filenames[i])
    #     row.append(hamming[i])
    #     row.append(num_variables[i])
    #     row.append(energy[i])
    #     row.append(model_time[i])
    #     row.append(solution_time[i])
    #     row_list.append(row)
    # with open(dirpath+'/analysis.json', 'w', newline='') as f:
    #     writer = csv.writer(csvfile)
    #     writer.writerows(row_list)
    with open(dirpath+'/analysis.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    f.close()

def main():

    parser = argparse.ArgumentParser(description="""
    This script is going to create an efficient assignment for the Tail Assignment Problem 
    By default the problem is modeled as a BQM direclty using parameters for encouraging or disencouraging some assignments.
    The default formulation assumes that at least a valid situation exists (no extra flights are needed)
    """)
    parser.add_argument("--filesdirectory", help="Path to the folder of the csv data files. Don't forget to follow the names' specifications")

    args = parser.parse_args()
    read_file(args.filesdirectory)


if __name__ == "__main__":
    main()
