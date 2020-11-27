"""

    Function:
    - reads the results generated from 2 different scripts
    - checks if the results are the same

    run in same directory as scripts to be checked

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

    #runs files to generate global_variable_table.csv and hmi_tag.csv
    os.system("python {}".format(old_script))
    print("{} ran successfully".format(old_script))
    os.system("mv global_variable_table.csv old_global_variable_table.csv")
    os.system("mv hmi_tag.csv old_hmi_tag.csv")

    os.system("python {}".format(new_script))
    print("{} ran successfully".format(new_script))
    os.system("mv global_variable_table.csv new_global_variable_table.csv")
    os.system("mv hmi_tag.csv new_hmi_tag.csv")

    #extract tables
    old_plc_table = pd.read_csv("old_global_variable_table.csv")
    new_plc_table = pd.read_csv("new_global_variable_table.csv")
    old_hmi_table = pd.read_csv("old_hmi_tag.csv")
    new_hmi_table = pd.read_csv("new_hmi_tag.csv")

    #check if plc tables are equal and find inconsistencies
    if new_plc_table.equals(old_plc_table):
        print ("\nGlobal Variable Tables are consistent")

    else :
        print ("\nGlobal Variable Tables are inconsistent")

        dataframe_difference(old_plc_table,new_plc_table)
    
    #check if hmi tables are equal and find inconsistencies
    if new_hmi_table.equals(old_hmi_table):
        print ("\nHMI Tag tables are consistent")

    else :
        print ("\nHMI Tag tables are inconsistent")

        dataframe_difference(old_plc_table,new_plc_table)

def dataframe_difference(df1, df2):

    compare = df1.merge(df2, how='outer', indicator=True)
    difference = compare[compare['_merge'] != 'both']
    print (difference)

    return difference

if __name__ == "__main__":
    main()