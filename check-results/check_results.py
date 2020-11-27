"""

    Function:
    - reads the results generated from 2 different scripts
    - checks if the results are the same

    To use:
    - run in same directory as scripts to be checked
    - in terminal, input "python check-results.py script1.py script2.py"

"""

from typing import Union
import sys
import os
import csv
import pandas as pd
import numpy as np

def main():

    #takes in files
    old_script = sys.argv[1]
    new_script = sys.argv[2]
    old_template = "global_variable_template.xlsx"
    new_template = "global_variable_template-new.xlsx"

    #runs files to generate global_variable_table.csv and hmi_tag.csv
    os.system("python {} {}".format(old_script,old_template))
    print("{} ran successfully\n".format(old_script))
    os.system("mv global_variable_table.csv old_global_variable_table.csv")
    os.system("mv hmi_tag.csv old_hmi_tag.csv")

    os.system("python {} {}".format(new_script,new_template))
    print("{} ran successfully\n".format(new_script))
    os.system("mv global_variable_table.csv new_global_variable_table.csv")
    os.system("mv hmi_tag.csv new_hmi_tag.csv")

    #extract names as tables
    old_plc_table = pd.read_csv("old_global_variable_table.csv")
    new_plc_table = pd.read_csv("new_global_variable_table.csv")
    old_hmi_table = pd.read_csv("old_hmi_tag.csv")
    new_hmi_table = pd.read_csv("new_hmi_tag.csv")

    old_plc_names = pd.DataFrame(old_plc_table['Identifiers'])
    new_plc_names = pd.DataFrame(new_plc_table['Identifiers'])
    old_hmi_names = pd.DataFrame(old_hmi_table['Define Name'])
    new_hmi_names = pd.DataFrame(new_hmi_table['Define Name'])

    #check if plc tables are equal and find inconsistencies
    if new_plc_names.equals(old_plc_names):
        print ("Global Variable Tables are consistent\n")

    else :
        print ("Global Variable Tables are inconsistent\n")

        difference = dataframe_difference(old_plc_names,new_plc_names)
        print (difference)

    #check if hmi tables are equal and find inconsistencies
    if new_hmi_names.equals(old_hmi_names):
        print ("HMI Tag tables are consistent\n")

    else :
        print ("HMI Tag tables are inconsistent\n")

        difference = dataframe_difference(old_plc_names,new_plc_names)
        print (difference)

def dataframe_difference(df1, df2):

    compare = df1.merge(df2, how='outer', indicator=True)
    difference = compare[compare['_merge'] != 'both']

    return difference

if __name__ == "__main__":
    main()