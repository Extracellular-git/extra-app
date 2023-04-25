import pandas as pd
import platemapping.plate_map as pm
#import extra_app.to_idot.doe_to_idot as dti

from doe_to_idot import calculate_target_well_info_per_df, get_source_wells, generate_csv_file


def generate_df_from_template(path_to_template:str, volume_dna:float, primers_volume:float, final_volume_without_master_mix:float, primer_tubes_choice:int):
    """
    This function takes excel template with well info and converts into a .csv file for the idot
    :param path_to_template:
    :param volume_dna:
    :param primers_volume:
    :param final_volume_without_master_mix:
    :param primer_tubes_choice:
    :return:
    """
    #importing the excel template file as a dataframe
    table = pd.read_excel(path_to_template, sheet_name='Sheet1')
    print(table)
    table.dropna(subset=['Group', 'Target'], inplace=True)
    #making a list of unique groups (removing duplicates)
    unique_groups = []
    for value in table.Group:
        if value not in unique_groups:
            unique_groups.append(value)
    #making a list of unique targets (removing duplicates)
    unique_targets = []
    #if there is only 1 tube of primers do the following
    if primer_tubes_choice == 1:
        for value in table.Target:
            if value not in unique_targets:
                unique_targets.append(value)

    #if there are 2 primer tubes, suffix with _1 or _2 (forward and reverse primer tubes)
    elif primer_tubes_choice == 2:
        for value in table.Target:
            if f'{value}_1' not in unique_targets:
                value_1 = f'{value}_1'
                unique_targets.append(value_1)
            if f'{value}_2' not in unique_targets:
                value_2 = f'{value}_2'
                unique_targets.append(value_2)

    print(f'unique_groups: {unique_groups}')
    print(f'unique_targets: {unique_targets}')
    #combining the lists of unique items generated above
    collated_list = unique_groups + unique_targets
    unique_targets_index = 0
    #making dataframe with unique groups and targets generated above
    df = pd.DataFrame(columns=collated_list)
    #making a column for water, filling water wells with 0 by default
    df['water'] = 0
    #defining a column for wells based on the original imported table
    df['Well'] = table['Wells']

    #print(f'first_df: {df}')
    # calculating how to populate the rest of the dataframe
    if primer_tubes_choice == 1:
        for i, row in enumerate(table['Group']):
            #calculating how much DNA volume to add to each well (row)
            df[row].iloc[i] = volume_dna/table['Dilution'].iloc[i]
            #working out how much water to top up to final volume (excluding master mix)
            df['water'].iloc[i] = final_volume_without_master_mix - ((volume_dna/table['Dilution'].iloc[i]) + primers_volume)
        #filling the primer column
        for i, row in enumerate(table['Target']):
            #print(f'row: {row}')
            df[row].iloc[i] = primers_volume
    # slightly different maths for 2 primer tubes vs 1
    elif primer_tubes_choice == 2:
        for i, row in enumerate(table['Group']):
            df[row].iloc[i] = volume_dna/table['Dilution'].iloc[i]
            df['water'].iloc[i] = final_volume_without_master_mix - ((volume_dna/table['Dilution'].iloc[i]) + (primers_volume*2))
        for i, row in enumerate(table['Target']):
            #print(f'row: {row}')
            df[f'{row}_1'].iloc[i] = primers_volume
            df[f'{row}_2'].iloc[i] = primers_volume
    #fill all other cells with 0
    df = df.fillna(0)
    print(df)

    # generating an empty plate map
    map = pm.empty_map()
    #creating a list of cols
    cols=[i for i in df.columns if i not in ["Well"]]
    #print(f'cols:{cols}')
    for col in cols:
        df[col]=pd.to_numeric(df[col])
    #needs to be in list for other code to work
    df = [df]
    return df, map


def qPCR_to_idot_main(path_to_template_file, path_to_output_file, volume_dna, primers_volume, final_volume_without_master_mix, primer_tubes_choice:int):
    """
    Main file bringing together the functions from this file and the doe_to_idot file
    :param path_to_template_file:
    :param path_to_output_file:
    :param volume_dna:
    :param primers_volume:
    :param final_volume_without_master_mix:
    :param primer_tubes_choice:
    :return:
    """

    df, map = generate_df_from_template(path_to_template_file, volume_dna, primers_volume, final_volume_without_master_mix, primer_tubes_choice)
    #print(df)
    sum_dictionary_list, starting_wells_dictionary_list = calculate_target_well_info_per_df(df, 1)
    #print(f'sum_dictionary_list: {sum_dictionary_list}, starting_wells_dictionary_list:{starting_wells_dictionary_list}')
    df = get_source_wells(df, sum_dictionary_list, starting_wells_dictionary_list, map)
    generate_csv_file(path_to_output_file, df, idot_header=True, dispense_plate='qpcr plate')

def plate_template_gen(path_to_template_file):
    """
    Generates a .csv file which works with the CFX instrument and analysis software
    :param path_to_template_file: str
    :return: dataframe in list
    """
    table = pd.read_excel(path_to_template_file, sheet_name='Sheet1')
    #print(f'table: {table}')
    table.dropna(subset=['Group', 'Target'], inplace=True)
    #print(f'table2: {table}')
    pt_df = pd.DataFrame(columns = ['Row','Column','*Target Name','*Sample Name','*Biological Group'])
    pt_df['Wells'] = table['Wells']
    for i, well in enumerate(table['Wells']):
        well_row = well[0]
        print(f'well_row:{well_row}')
        well_column = well[1:]
        pt_df['Row'].iloc[i] = well_row
        pt_df['Column'].iloc[i] = well_column
    for i, group in enumerate(table['Group']):
        pt_df['*Sample Name'].iloc[i] = str(group)
    for i, target in enumerate(table['Target']):
        pt_df['*Target Name'].iloc[i] = str(target)
    pt_df.drop(['Wells'], axis=1, inplace=True)
    return [pt_df]


if __name__ == '__main__':
    # template_file = input('Please provide the path to the template ')
    # idot_choice = input('Are you plating the assay with the idot? (y/n) ')
    # if idot_choice == 'y':
    #     idot_output_file = input('Please provide a path for the idot output file (as a .csv file) ')
    #     dna_volume = float(input('What volume of DNA mixture per well as a number in ul (e.g. "1") '))
    #     primer_number_choice = int(input('How many tubes of primers do you have with this assay? (i.e. "1" or "2" )'))
    #     primer_volume = float(input('What volume of each primer per well as a number in ul (e.g. "1") '))
    #     reaction_volume = float(input('Please provide the final reaction volume per well as a number in ul (e.g. "10") '))
    #     df = qPCR_to_idot_main(template_file, idot_output_file, dna_volume, primer_volume, reaction_volume/2, primer_number_choice)
    # qpcr_choice = input('Would you like to make a qPCR plate template? (y/n) ')
    # #CHANGE THIS BACK TO VARS
    # if qpcr_choice == 'y':
    #     qPCR_output_file = input('Please provide a path for the idot output file (as a .csv file) ')
    #     df = plate_template_gen(template_file)
    #     dti.generate_csv_file(qPCR_output_file, df, idot_header=False)

    #df = qPCR_to_idot_main('qPCR_assay_template_ipsc test.xlsx', '21Mar23_qpcr.csv', 2, 1, 5, 1)
    df = plate_template_gen('qPCR_assay_template_ipsc test.xlsx')
    generate_csv_file('21Mar23_qpcr_template.csv', df, idot_header=False)