"""
    Global Variable Generator:

    Function:
    - generate a csv file that contains all shelf-related global variable
      based on the inputs in global_variable_template.xlsx
    - csv file can be imported into Delta ISPSoft

    How to use:
    - configure parameter in global_variable_template.xlsx
    - run this script at the same directory as global_variable_template.xlsx
    - global_variable_table.csv will be generated upon script completion
"""

from typing import Union
import os
import csv
import pandas as pd
import numpy as np


def main():

    # parameter
    input_name = "global_variable_template_new.xlsx"
    global_var_table_name = "global_variable_table.csv"
    hmi_tag_table_name = "hmi_tag.csv"
    hmi_tag_plc_name = "{EtherLink1}1@"

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    dir_name = os.path.join(curr_dir, input_name)

    # extract tables from excel
    constant_table = pd.read_excel(dir_name, sheet_name="Constants")
    shelf_table = pd.read_excel(dir_name, sheet_name="Shelf")
    sensor_list_table = pd.read_excel(dir_name, sheet_name="Sensor List")
    sensor_data_table = pd.read_excel(dir_name, sheet_name="Sensor Data")
    pump_data_table = pd.read_excel(dir_name, sheet_name="Pump")
    io_mapping_table = pd.read_excel(dir_name, sheet_name="IO Mapping")
    hmi_data_table = pd.read_excel(dir_name, sheet_name="HMI Internal")

    # read data from tables
    constant_base_addr, constants = read_var_table(constant_table)
    shelf_base_addr, shelfs = read_var_table(shelf_table)
    sensor_base_addr, sensors = read_sensor_list_table(sensor_list_table)
    sens_base_addr, sensor_data = read_var_table(sensor_data_table)
    pump_base_addr, pumps = read_var_table(pump_data_table)
    io_data = read_io_mapping_table(io_mapping_table)
    hmi_base_addr, hmi_internal = read_hmi_internal_table(hmi_data_table)

    # define common properties
    shelf_no = constants['shelf_no']['init_value']
    shelf_reg_size = constants['shelf_reg_size']['init_value']

    # ensure user has defined shelf_no and shelf_reg_size
    assert("shelf_no" in constants) and ("shelf_reg_size" in constants) == True

    global_var_table = {}
    hmi_tag_table = {}

    # parse constants and write into global_var_table
    constant_curr_addr = constant_base_addr
    for var_name in constants:
        var_data = constants[var_name]
        
        constant_curr_addr += int(var_data['addr_offset'])
        addr = "D{}".format(round(float(constant_curr_addr), 1) if "BOOL" in var_data['type'] else int (constant_curr_addr) )
        
        write_rec_glob_var_table(global_var_table, var_name, addr, var_data['type'], var_data['init_value'])

    # parse pump_data and write into global_var_table
    pump_curr_addr = pump_base_addr
    for var_name in pumps:
        pump_data = pumps[var_name]

        addr = "D{}".format( round(float(pump_curr_addr), 1) if "BOOL" in pump_data['type'] else int (pump_curr_addr) )
        pump_curr_addr += int(pump_data['addr_offset'])

        write_rec_glob_var_table(global_var_table, var_name, addr, pump_data['type'], pump_data['init_value'])
        
    # parse shelfs and write into global_var_table
    for i in range(shelf_no):
        shelf_curr_addr = shelf_base_addr + i * shelf_reg_size
        for var_name in shelfs:
            shelf_data = shelfs[var_name]
            name = "s{}_{}".format(i, var_name)

            addr = "D{}".format( round(float(shelf_curr_addr), 1) if "BOOL" in shelf_data['type'] else int (shelf_curr_addr))
            shelf_curr_addr += int(shelf_data['addr_offset'])

            write_rec_glob_var_table(global_var_table, name, addr, shelf_data['type'], shelf_data['init_value'])
    
    # parse constants and write into hmi_tag_table
    constant_curr_addr = constant_base_addr
    for var_name in constants:
        var_data = constants[var_name]

        # filter those that should go into hmi_tag
        if not var_data['hmi_tag']:
            constant_curr_addr += var_data['addr_offset']
            continue

        # check if variable is an array
        if "ARRAY" in var_data['type']:
            array_size = get_array_size(var_data['type'])
            array_type = get_array_type(var_data['type'])
            constant_arr_addr = constant_curr_addr

            for j in range(array_size):
                name = f"{var_name}{j}"
                addr_offset = calc_addr_offset_hmi_tag(is_array=True, var_type=array_type, 
                                                       offset=var_data['addr_offset'])
                var_type = translate_var_type_hmi_tag(var_type=array_type)

                addr = hmi_tag_plc_name + \
                       "D{}".format( round(float(constant_arr_addr), 1) if "BOOL" in var_data['type'] else int (constant_arr_addr) )
                
                constant_arr_addr += addr_offset
                write_rec_hmi_tag_table(hmi_tag_table, name, var_type, addr)

            constant_curr_addr += var_data['addr_offset']

        # non-array variable
        else:
            name = f"{var_name}"
            addr_offset = calc_addr_offset_hmi_tag(is_array=False, var_type=var_data['type'], 
                                                offset=var_data['addr_offset'])
            var_type = translate_var_type_hmi_tag(var_type=var_data['type'])
            addr = hmi_tag_plc_name + \
                "D{}".format( round(float(constant_curr_addr), 1) if "BOOL" in shelf_data['type'] else int (constant_curr_addr))

            write_rec_hmi_tag_table(hmi_tag_table, name, var_type, addr)
            constant_curr_addr += addr_offset
    
    # parse pump_data and write into hmi_tag_table
    pump_curr_addr = pump_base_addr
    for var_name in pumps:
        pump_data = pumps[var_name]

        # filter those that should go into hmi_tag
        if not pump_data['hmi_tag']:
            pump_curr_addr += pump_data['addr_offset']
            continue

        # check if variable is an array
        if "ARRAY" in pump_data['type']:
            array_size = get_array_size(pump_data['type'])
            array_type = get_array_type(pump_data['type'])
            pump_arr_addr = pump_curr_addr

            for j in range(array_size):
                name = f"{var_name}{j}"
                addr_offset = calc_addr_offset_hmi_tag(is_array=True, var_type=array_type, 
                                                       offset=pump_data['addr_offset'])
                var_type = translate_var_type_hmi_tag(var_type=array_type)

                addr = hmi_tag_plc_name + \
                       "D{}".format( round(float(pump_arr_addr), 1) if "BOOL" in pump_data['type'] else int (pump_arr_addr) )
                
                pump_arr_addr += addr_offset
                write_rec_hmi_tag_table(hmi_tag_table, name, var_type, addr)

            pump_curr_addr += pump_data['addr_offset']

        # non-array variable
        else:
            name = f"{var_name}"
            addr_offset = calc_addr_offset_hmi_tag(is_array=False, var_type=pump_data['type'], 
                                                   offset=pump_data['addr_offset'])
            var_type = translate_var_type_hmi_tag(var_type=pump_data['type'])

            addr = hmi_tag_plc_name + \
                   "D{}".format( round(float(pump_curr_addr), 1) if "BOOL" in shelf_data['type'] else int (pump_curr_addr))

            write_rec_hmi_tag_table(hmi_tag_table, name, var_type, addr)
            pump_curr_addr += addr_offset
        
    # parse shelfs and write into hmi_tag_table
    for i in range(shelf_no):
        shelf_curr_addr = shelf_base_addr + i * shelf_reg_size
        for var_name in shelfs:
            shelf_data = shelfs[var_name]

            # filter those that should go into hmi_tag
            if not shelf_data['hmi_tag']:
                shelf_curr_addr += shelf_data['addr_offset']
                continue

            # check if variable is an array
            if "ARRAY" in shelf_data['type']:
                array_size = get_array_size(shelf_data['type'])
                array_type = get_array_type(shelf_data['type'])
                shelf_arr_addr = shelf_curr_addr

                for j in range(array_size):
                    name = f"s{i}_{var_name}{j}"

                    addr_offset = calc_addr_offset_hmi_tag(is_array=True, var_type=array_type,
                                                           offset=shelf_data['addr_offset'])
                    var_type = translate_var_type_hmi_tag(var_type=array_type)

                    addr = hmi_tag_plc_name + \
                           "D{}".format( round(float(shelf_arr_addr),1) if "BOOL" in shelf_data['type'] else int (shelf_arr_addr))
                    
                    shelf_arr_addr += addr_offset
                    write_rec_hmi_tag_table(hmi_tag_table, name, var_type, addr)

                shelf_curr_addr += shelf_data['addr_offset']

            # non-array variable
            else:
                name = f"s{i}_{var_name}"

                addr_offset = calc_addr_offset_hmi_tag(is_array=False, var_type=array_type, offset=shelf_data['addr_offset'])
                var_type = translate_var_type_hmi_tag(var_type=shelf_data['type'])

                addr = hmi_tag_plc_name + \
                        "D{}".format( round(float(shelf_curr_addr), 1) if "BOOL" in shelf_data['type'] else int (shelf_curr_addr))

                write_rec_hmi_tag_table(hmi_tag_table, name, var_type, addr)
                shelf_curr_addr += addr_offset

    # parse sensors, sensor_data and write into global_var_table
    # parse sensors, sensor_data and write into hmi_tag_table
    addr_offset = 1
    for i in range(shelf_no):
        for snsr_name in sensors['shelf_sensors']:
            for j, var_name in enumerate(sensor_data):
                data = sensor_data[var_name]
                name = "snsr_s{}_{}_{}".format(i, snsr_name, var_name)
                
                # for global_var_table
                addr = "D{}".format(sensor_base_addr + addr_offset)
                write_rec_glob_var_table(global_var_table, name, addr, data['type'], data['init_value'])

                # for hmi_tag_table
                addr = hmi_tag_plc_name + "D{}".format(sensor_base_addr + addr_offset)
                write_rec_hmi_tag_table(hmi_tag_table, name, data['type'], addr)

                addr_offset += 1

    for snsr_name in sensors['other_sensors']:
        for i, var_name in enumerate(sensor_data):
            data = sensor_data[var_name]
            name = "snsr_{}_{}".format(snsr_name, var_name)

            # for global_var_table
            addr = "D{}".format(sensor_base_addr + addr_offset)
            write_rec_glob_var_table(global_var_table, name, addr, data['type'], data['init_value'])
            
            # for hmi_tag_table
            addr = hmi_tag_plc_name + "D{}".format(sensor_base_addr + addr_offset)
            write_rec_hmi_tag_table(hmi_tag_table, name, data['type'], addr)
            
            addr_offset += 1

    
    # parse io_data and write into global_var_table & hmi_tag_table
    for io_name in io_data:
        io = io_data[io_name]
        write_rec_glob_var_table(global_var_table, io_name, io['addr'], io['type'], io['init_value'])

        if io['hmi_tag']:
            addr = hmi_tag_plc_name + io['addr']
            write_rec_hmi_tag_table(hmi_tag_table, io_name, io['type'], addr)


    # parse hmi_internal and write into hmi_tag_table
    hmi_curr_addr =  hmi_base_addr
    for var_name in hmi_internal:

        addr = "$"
        hmi_data = hmi_internal[var_name]
        if hmi_data['type'] == "BIT":
            addr += str(round(float(hmi_curr_addr), 1))
        elif hmi_data['type'] == "WORD":
            addr += str(hmi_curr_addr)
        else:
            raise RuntimeError("Invalid type")

        write_rec_hmi_tag_table(hmi_tag_table, var_name, hmi_data['type'], addr)
        hmi_curr_addr += int(hmi_data['addr_offset'])

    # write global_var_table into global_variable_table.csv
    write_glob_var_table_to_csv(global_var_table_name, global_var_table)

    # write hmi_tag_table into hmi_tag_table.csv
    write_hmi_tag_table_to_csv(hmi_tag_table_name, hmi_tag_table)

def read_var_table(s_table: dict) -> dict:
    s_dict = {}
    if s_table['base_addr'].tolist()[0] != "-":
        s_base_addr = int(s_table['base_addr'].tolist()[0])
    else:
        s_base_addr = 0
    s_names = s_table['variable_name'].tolist()
    s_addr_offsets = s_table['addr_offset'].tolist()
    s_types = s_table['type'].tolist()
    s_init_values = s_table['init_value'].tolist()
    s_hmi_tags = s_table['hmi_tag'].tolist()

    # inject name, addr_offset, type, init_value
    for s_name, s_addr_offset, s_type, s_init_value, s_hmi_tag \
        in zip (s_names, s_addr_offsets, s_types, s_init_values, s_hmi_tags):

        s_dict[s_name] = {
            'addr_offset': s_addr_offset,
            'type': s_type,
            'init_value': s_init_value,
            'hmi_tag': True if not pd.isna(s_hmi_tag) else False
            }

    return s_base_addr, s_dict

def read_sensor_list_table(sl_table: dict) -> dict:
    sl_dict = {}
    sl_base_addr = int(sl_table['base_addr'].tolist()[0])
    shelf_sensors = [x for x in sl_table['shelf_sensor'].tolist() if not pd.isna(x)]
    other_sensors = [x for x in sl_table['general_sensor'].tolist() if not pd.isna(x)]

    sl_dict['shelf_sensors'] = shelf_sensors
    sl_dict['other_sensors'] = other_sensors

    return sl_base_addr, sl_dict


def read_io_mapping_table(io_table: dict) -> dict:
    io_dict = {}
    var_names = io_table['variable_name'].tolist()
    var_addrs = io_table['addr'].tolist()
    var_types = io_table['type'].tolist()
    var_init_values = io_table['init_value'].tolist()
    var_hmi_tags = io_table['hmi_tag'].tolist()

    # inject name, addr_offset, type, init_value
    for io_name, io_addr, io_type, io_init_value, io_hmi_tag \
        in zip (var_names, var_addrs, var_types, var_init_values, var_hmi_tags):

        io_dict[io_name] = {
            'addr': io_addr,
            'type': io_type,
            'init_value': io_init_value,
            'hmi_tag': True if not pd.isna(io_hmi_tag) else False
            }

    return io_dict


def read_hmi_internal_table(h_table: dict) -> dict:
    h_dict = {}
    h_base_addr = int(h_table['base_addr'].tolist()[0])
    h_names = h_table['var_name'].tolist()
    h_addr_offsets = h_table['addr_offset'].tolist()
    h_types = h_table['var_type'].tolist()

    # inject name, addr_offset, type
    for h_name, h_addr_offset, h_type in zip (h_names, h_addr_offsets, h_types):
        h_dict[h_name] = {
            'addr_offset': h_addr_offset,
            'type': h_type,
        }

    return h_base_addr, h_dict


def write_rec_glob_var_table(
    global_var_table: dict, var_name: str, var_addr: str, \
    var_type: str, var_init_value: str) -> None:

    global_var_table[var_name] = {
        "addr": var_addr,
        "type": var_type,
        "init_value": var_init_value
    }

    return


def write_glob_var_table_to_csv(filename, global_var_table):
    header = ["Class", "Identifiers", "Address", "Type", "Initial Value", "Comment"]
    curr_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(curr_dir, filename), mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)

        for var_name in global_var_table:
            var_data = global_var_table[var_name]
            writer.writerow(['VAR', var_name, var_data['addr'], var_data['type'], var_data['init_value']])

    print("completed: global_variable_table.csv")


def write_rec_hmi_tag_table(
    table: dict, var_name: str, var_type: str, var_addr: str) -> None:

    table[var_name] = {
        "type": var_type,
        "addr": var_addr
    }

    return


def write_hmi_tag_table_to_csv(filename, hmi_tag_table):
    header = ['Define Name', 'Type', 'Address', 'Description']
    curr_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(curr_dir, filename), mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)

        for var_name in hmi_tag_table:
            var_data = hmi_tag_table[var_name]
            writer.writerow([var_name, var_data['type'], var_data['addr']])

    print("completed: hmi_tag_table.csv")


def calc_addr_offset_hmi_tag(is_array: bool, var_type: str, offset: str) -> Union[int, float]:
    if var_type == "BOOL":
        return (0.1) if is_array else float(offset)
    elif var_type == "WORD":
        return (1) if is_array else int(offset)
    else:
        raise RuntimeError("Invalid type")

def translate_var_type_hmi_tag(var_type: str) -> str:
    if var_type == "BOOL":
        return "BIT"
    elif var_type == "WORD":
        return "WORD"
    else:
        raise RuntimeError("Invalid type")


def get_array_size(data: str) -> int:
    tmp = data.split(' ')
    return int(tmp[1].replace('[', '').replace(']',''))


def get_array_type(data: str) -> int:
    return data.split(' ')[3]


if __name__ == "__main__":
    main()