#!/usr/bin/env python3
import pandas as pd

from local_print_tool import get_table_data, trim_table_data

def reformat_opvia_date(raw_opvia_date) -> str:
    """
    reformats the opvia date output from yyyy-mm-ddTHH:MM:SS:sssZ to dd/MMM/yyyy
    :param raw_opvia_date: the raw opvia date string to be reformatted.
    :return: the formatted date string.
    """
    # Check for and except empty input.
    if raw_opvia_date != "":
        day = raw_opvia_date[8:10]
        month = raw_opvia_date[5:7]
        year = raw_opvia_date[0:4]
        month_dict = {
            "01":"Jan",
            "02":"Feb",
            "03":"Mar",
            "04":"Apr",
            "05":"May",
            "06":"Jun",
            "07":"Jul",
            "08":"Aug",
            "09":"Sep",
            "10":"Oct",
            "11":"Nov",
            "12":"Dec"
        }
        format_exp_date = day + "/" + month_dict[month] + "/" + year

        return format_exp_date
    else:
        return "no date"


def format_cell_number(cell_number: int) -> str:
    """
    Takes in a large sci-notation number and formats it to have k/m/b instead of e3, e6, e9 etc.
    only works for those options.
    :param cell_number: cell number as raw int.
    :return: formatted string eg. 1.5e9 -> 1.5B
    """
    cell_number = int(cell_number)
    cell_number_decimal = 0
    char = ""
    if len(str(cell_number)) >= 9:
        cell_number_decimal = cell_number / 1000000000
        char = "B"
    elif len(str(cell_number)) >= 6:
        cell_number_decimal = cell_number / 1000000
        char = "M"
    elif len(str(cell_number)) >= 3:
        cell_number_decimal = cell_number / 1000
        char = "K"

    cell_number_str = str(round(cell_number_decimal, 1))

    return cell_number_str + char


def format_cell_number_branchless(cell_number: int) -> str:
    """
    NOTE: This branchless version is actually about 4x slower than the branched version, do not use.
    Takes in a large sci-notation number and formats it to have k/m/b instead of e3, e6, e9 etc.
    only works for those options.
    :param cell_number: cell number as raw int.
    :return: formatted string eg. 1.5e9 -> 1.5B
    """
    return (
            (str(round(cell_number / 1000000000, 1)) + "B") * (len(str(cell_number)) >= 9)
            + (str(round(cell_number / 1000000, 1)) + "M") * (8 >= len(str(cell_number)) >= 6)
            + (str(round(cell_number / 1000, 1)) + "K") * (5 >= len(str(cell_number)) >= 3)
    )


def get_media_composition(comp_list: list) -> list:
    """
    takes a list of compositions of a media and returns a list of strings containing the
    component name and concentration. if percent is empty, use comment.
    :param comp_list:
    :return: comp_string_list
    """

    comp_table_id = "1f1acdb8-87a7-4681-9371-225cb7d9320c"
    comp_string_list = []

    comp_df = get_table_data(comp_table_id)

    # Set the index of the table to the Composition ID to allow searching.
    comp_df.set_index("Composition ID", inplace=True, verify_integrity=False, drop=False)
    # Select and save the records that match the ID's in the id_list.
    trim_comp_df = pd.DataFrame()
    # Iteratively, so that non-existent IDs can be caught and handled.
    for each_id in comp_list:
        try:
            trim_comp_df = pd.concat([trim_comp_df, comp_df.loc[each_id]], axis=1)

        except KeyError:
            print(f"No item exists for ID: {each_id}")
    # Fix wrong orientation from weird concatenation
    trim_comp_df = trim_comp_df.transpose()
    # Replace NaN with empty string.
    trim_comp_df.fillna("", inplace=True)

    comp_dict_list = trim_comp_df.to_dict("records")

    for comp_dict in comp_dict_list:
        comp_string_list.append(str(comp_dict["Percentage Concentration"]) + "% " + str(comp_dict["Description"]))

    return comp_string_list
