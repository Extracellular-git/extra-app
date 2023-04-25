from pathlib import Path

import csv
import datetime
import math
import numpy as np
import pandas as pd
import platemapping.plate_map as pm


def generate_target_vols(csv_path, final_volume, starting_conc_dict, replicates=1, orientation='by_columns'):
    """
    creates a target plate dataframe, containing the volumes to be added to each well (row). 
    :param csv_path: doe template file (see SOP for more info)
    :param final_volume: volume of each well
    :param starting_conc_dict: dictionary detailing every reagents starting (stock) dilution
    :param replicates: Number of replicates per well/condition
    :param orientation: how the plate is dispensed, by columns is default, anything else will be taken as by rows
    :return:
    """
    # read the .csv doe file
    doe = pd.read_csv(csv_path, index_col=False)
    # creating lists/dicts for data storage
    col_list = []
    # makes a list of column names from the doe dataframe
    for col in doe.columns:
        col_list.append(col)
    # drop unneeded column if there
    if 'Unnamed: 0' in col_list:
        doe.drop('Unnamed: 0', axis=1, inplace=True)
    # iterates through the list of coolumn headers
    for col in col_list:
        #print(col)
        temp_list = []
        # iterates through every element in a column
        for element in doe[col]:
            # if the concentration is 0 then add is 0
            if element == 0:
                add = 0
            # if concentration in column is not 0 then divide the starting concentration by the target concentration to get the dilution factor
            else:
                dilution_factor = starting_conc_dict[col] / element
                #calculate how much to add
                add = final_volume / dilution_factor
                #have put a round in here, if this isn't hear then there are times where the volume doesn't quite reach the target by some ridiculously small amount, 
                #leading to problems
                add = round(add, 4)
            # append the calculated volume to the list
            temp_list.append(add)
           # print(add)
        # replace the column in doe with the list of amounts to add
        doe[col] = temp_list
        # print(f'column_sum_dict:{column_sum_dict}')
    # replicates the values a number of times as defined in the replicates argument
    if replicates != 1:
        doe = pd.DataFrame(np.repeat(doe.values, replicates, axis=0))
        #print(doe)
    doe.columns = col_list
    
    # generating an empty plate map
    map = pm.empty_map()
    # getting the wells from the map
    wells = map.index
    # gets the length of the plate in rows
    len_doe_plate = len(doe)
    
    # if the orientation is not by columns (default) then some code to do by rows
    if orientation != 'by_columns':
        wells = pd.Series(wells)
        #making loads of replicates of the well names to accommodate any number of plates 
        wells_repeated = pd.concat([wells]*100, ignore_index=True)
        #truncates the number of wells by the length of the plate
        correct_length_wells = wells_repeated[0:len_doe_plate]
        #print(f'correct wells list: {correct_length_wells}')
        doe['Well'] = correct_length_wells
        
    else:
        by_columns_list = []
        for i in range(12):
            temp_list = list(wells[i::12])
            #print(f'temp_list: {temp_list}')
            by_columns_list = by_columns_list + temp_list
            ##print(f'by columns list: {by_columns_list}')
        wells = pd.Series(by_columns_list)
        #making loads of replicates of the well names to accommodate any number of plates (removes chance of index error) 
        wells_repeated = pd.concat([wells]*100, ignore_index=True)
        #truncates the number of wells by the length of the plate
        correct_length_wells = wells_repeated[0:len_doe_plate]
        #creating a well column with the correct length of wells
        doe['Well'] = correct_length_wells
    #converting series into a list of groups of 96 (i.e. by plate-sized chunks)
    list_df = [doe[i:i+96] for i in range(0,doe.shape[0],96)]
    for df in list_df:
        #resetting the indices of each df
        df.reset_index(drop=True, inplace=True)
    return list_df, map

def calculate_target_well_info_per_df(df_list, replicates):
    """
    Calculates the total reagent volumes and the number of source wells required to cover the reagent volumes
    :param df_list: the list of dataframes corresponding to plates
    :param replicates: the number of replicates per sample/condition
    :return:
    sum_dictionary_list: the volume of reagent
    starting_wells_dictionary_list: the number of source wells required per reagent
    """
    sum_dictionary_list = []
    starting_wells_dictionary_list = []
    for df in df_list:
        print(f'df: {df}')
        col_list = []
        temp_list = []
        column_sum_dict = {}
        starting_wells_count_dict = {}
        starting_wells_volume_dict = {}
        for col in df.columns:
            col_list.append(col)
        #iterates through the column list, except for the wells
        for col in col_list[:-1]:
            temp_list = df[col]
            #get the sum total of a reagent in the list
            col_sum = round(float(np.sum(temp_list)), 5) 
            #define the sum volume as an element in the dictionary
            column_sum_dict[col] = col_sum
        for i in column_sum_dict:
            print(i, type(i))
            #calculate the number of source wells required per reagent
            if column_sum_dict[i] <=80:
                starting_wells_count_dict[i] = 1
            elif column_sum_dict[i] >80:
                starting_wells_count_dict[i] = math.ceil(column_sum_dict[i]/80)
                starting_wells_volume_dict[i] = round(float(column_sum_dict[i]/starting_wells_count_dict[i]),5)
        #calculates the total number of starting wells required
        total_starting_wells = np.sum(starting_wells_count_dict.values())
        print(f'ts: {total_starting_wells}')
        sum_dictionary_list.append(column_sum_dict)
        starting_wells_dictionary_list.append(starting_wells_count_dict)
    return sum_dictionary_list, starting_wells_dictionary_list

def get_source_wells(list_df, sum_wells_list, num_wells_list, map):
    """
    Generates a dataframe containing the source well information as well as the target well information for each reagent added to the plates
    :param list_df: list of dataframes corresponding to each plate
    :param sum_wells_list: total volume per reagent
    :param num_wells_list: total source wells per reagent
    :param map: the map generated in a previous function (containing the wells)
    :return:
    df_list: list of dataframes detailing the volumes of each reagent to be dispensed
    """
    df_list = []
    source_well_index = 0
    for dict_index, df in enumerate(list_df):
        #getting all of the number wells per substance dictionary keys and including in a list
        dict_keys = list(num_wells_list[dict_index].keys())
        #getting all of the number of wells per substance dictionary values and including in a list
        dict_values = list(num_wells_list[dict_index].values())
        df.reset_index(drop=True)
        #count the number of loops, starting at 0, obviously
        iter_count = 0
        #full_plate_list = [96, 192, 288, 384, 480, 576, 672, 768, 864, 960, 1056, 1152, 1248, 1344, 1440, 1536, 1632, 1728, 1824, 1920, 2016, 2112, 2208, 2304, 2400, 2496, 2592, 2688, 2784, 2880, 2976, 3072, 3168, 3264, 3360, 3456, 3552, 3648, 3744, 3840, 3936, 4032, 4128, 4224, 4320, 4416, 4512, 4608, 4704, 4800, 4896, 4992, 5088, 5184, 5280, 5376, 5472, 5568, 5664, 5760, 5856, 5952, 6048, 6144]
        #creating new df with correct titles 
        new_df = pd.DataFrame(columns = ['Source Well', 'Target Well', 'Volume [ul]', 'Liquid Name','','','','',''])
        # making a list of reagents, e.g. [Substance A, Substance A, Substance B, Substance C, Substance C]. This makes it easier to index the correct reagent
        source_reagent_list = []
        for i in range (len(dict_keys)):
            well = [dict_keys[i]] * dict_values[i]
            source_reagent_list = source_reagent_list + well 
        #getting a list of plate wells for the source reagents
        source_wells_list = map.index
        #getting the length of the source reagents list
        num_source_wells = len(source_reagent_list)
        #truncating the source wells according to the length 
        source_wells_list = source_wells_list[:num_source_wells*len(df.columns[:-1])*len(list_df)]
        #iterate through each column from the target dataframe
        for column in df.columns[:-1]: 
            #source_wells = 0
            one_column_iteration_count = 1
            # counter for volume of all of the source wells of 1 reagent
            total_reagent_counter = 0
            # counter for the volume taken from 1 well
            volume_counter = 0
            #making a list from reagents
            temp_list = df[column]
            # making a list from the wells
            well_list = df['Well']
            #print(well_list)
            for reagent_list_index, value in enumerate(temp_list):
                value = round(float(value),5)
                if value == 0:
                    volume_counter = round(float(volume_counter + value),5)
                    iter_count = iter_count + 1
                # if there is something to add to a well, do something
                elif value != 0.0:
                    # keeping track of the volume from one well
                    volume_counter = round(float(volume_counter + value),5)
                    #keeping track of volume from all wells of 1 reagent
                    total_reagent_counter = round(float(total_reagent_counter + value),5)
                    #if the max volume from one well has been reached, change index of source well
                    if volume_counter > 79.99:
                        source_well_index=source_well_index+1
                        #reset the volume added to reflect the amount from the new source reagent well
                        volume_counter = value
                    #if the total volume is equal to the total reagent volume then break the loop and start
                    #generating one row, equating to addition to one well, blanks to get correct shape
                    one_row =  [source_wells_list[source_well_index], well_list[reagent_list_index], value, column,'' ,'' ,'' ,'' ,'' ]
                    #adding the row to the df
                    new_df.loc[iter_count] = one_row
                    iter_count = iter_count + 1
                    print(f'sum_wells_list[dict_index][column]: {sum_wells_list[dict_index][column]}')
                    print(f'total_reagent_counter:{total_reagent_counter}')
                    #if the total reagent is equal to the total amount calculated, skip to the next source well and break 
                    if total_reagent_counter >= sum_wells_list[dict_index][column]:
                        source_well_index=source_well_index+1
                        break
                    #or if the number of source well iterations is equal to the total source wells, move on and break (this is a fail safe for the above)
                    elif one_column_iteration_count == len(temp_list):
                        source_well_index=source_well_index+1
                        break
                one_column_iteration_count += 1 
                print(one_column_iteration_count)
        new_df = new_df.reset_index(drop=True)
        df_list.append(new_df)
    return df_list

def generate_csv_file(csv_path, list_df, idot_header=True, dispense_plate='MWP 96'):
    """
    Creates a csv file from dataframe in a format suitable for the iDOT
    :param csv_path: path to .csv file
    :param list_df: list of dataframes to append into one file
    :param idot_header: whether or not to include the header in the .csv
    :param dispense_plate: this will change whether it is for plating into the standard assay plates, or the qPCR plate
    :return:
    """
    Path(csv_path).touch()

    date = datetime.date.today()
    
    for plate_number, df in enumerate(list_df): 
        plate_num = plate_number +1
        #print(f'df: {df}')
        if idot_header == True:
            rows =[[date, '1.9.1.5', '<User Name>', date,'','',''],
                ['S.100 Plate',f'Source Plate {1}','', 8.00E-05, dispense_plate, plate_num,'','Waste Tube'],
                ['DispenseToWaste=True','DispenseToWasteCycles=3','DispenseToWasteVolume=1e-7','UseDeionisation=True','OptimizationLevel=ReorderAndParallel','WasteErrorHandlingLevel=Ask','SaveLiquids=Ask','']]
            with open(csv_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
                #print(f'df: {df}')
        df.to_csv(csv_path, mode='a', header=True, index=False)
        
 
def doe_to_idot_main(doe_csv_path, final_volume, starting_conc_dict, final_csv_path, replicates=1, orientation='by_columns'):
    """
    Brings all the above functions together
    :param doe_csv_path: source template .csv file
    :param final_volume: the final volume in each well
    :param starting_conc_dict: dictionary of the starting concentrations for the reagents
    :param final_csv_path: the output path for the iDOT .csv file
    :param replicates: the number of replicates per well/condition
    :param orientation: by columns or by rows. Default is by columns
    :return:
    """
    df_list_first, map = generate_target_vols(doe_csv_path, final_volume, starting_conc_dict, replicates=replicates, orientation=orientation)
    #print(df_list_first)
    sum_wells_list, num_wells_list = calculate_target_well_info_per_df(df_list_first, replicates)
    print(sum_wells_list, num_wells_list)
    final_df_list = get_source_wells(df_list_first, sum_wells_list, num_wells_list, map)
    #print(final_df_list)
    generate_csv_file(final_csv_path, final_df_list)
    


if __name__ == '__main__':
    # Note: the units for the starting concentrations and the target concentrations (from the DoE) must be the same
    starting_conc_dict = {'ITS (X)':100, 'DEX (uM)': 2.55, 'LASC (mM)':283.89, 'TGF-B1 (ng/mL)':100, 'FGF-2 (ng/mL)':2000,'PDGF-b (ng/mL)': 1000, 'LA (X)': 100}
    doe_to_idot_main('21Mar23_doe_conditions_one_plate.csv', 200, starting_conc_dict, '21Mar23_for_idot_by_rows.csv', replicates = 1, orientation ='by_rows')
