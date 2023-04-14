import os
import re
import tempfile
import toml

import pandas as pd
import pyrebase
import requests
import Crypto


from ftplib import FTP
from .my_secrets import get_username, get_password
from io import TextIOWrapper
from os import path


# build script:
# python -m PyInstaller .\printing\labelscripts\local_print_tool.py -i .\printing\labelscripts\print_icon.ico  --onefile --clean --hidden-import PyCryptodome --hidden-import Crypto --noupx


def expand_hyphen(input: str) -> list:
    """
    Takes input of one hyphenated ID range, eg. I1000003-I1000006 and returns a list of every id in that range,
    inclusive.
    :param input:
    :return:
    """

    id_chars = re.split('(\d+)', input)[0]
    id_range = input.split("-")
    if len(id_range[0]) == 8 and len(id_range[1]) == 8:
        id_range = [int(re.sub("\D", "", x)) for x in id_range]
        id_num_range = range(id_range[0], id_range[1] + 1)
        out_list = [f"{id_chars}{str(id_num)}" for id_num in id_num_range]
    else:
        print(f"Incorrectly formatted range: {input}")
        out_list = []

    return out_list


def expand_multiply(input: str) -> list:
    """
    Takes input of one mulitplied ID or ID range, and returns a list of that item, the count being multiplied.
    eg I1000004*3 -> I1000004, I1000004, I1000004
    :param input: ID string with multiplier x or * in it.
    :return list: list of multiplied IDs
    """

    input = re.sub("x", "*", input)
    split_input = input.split("*")
    mult = int(split_input[1])
    out_list = [split_input[0] for idx in range(mult)]

    return out_list


def user_label_selection() -> list:
    """
    This function takes input from the user on the range of labels they would like to print by using the item ID, and
    returns these as a list of item ID's.
    :return list: list of item ID's for desired labels to print.
    """
    print("""Please enter an ID or range of IDs. Or, copy and paste from Opvia.
Separate individual ID's with commas, and specify a range using a hyphen. Specify repeats using * or x.
Only enter one type of ID at a time.
### Type "s" or "ns" for Sterile or Not-Sterile labels. ###
""")
    raw_list = []
    out_list = []
    # ends when this string is seen
    end_char = ''
    for line in iter(input, end_char):
        raw_list.append(line)

    # Check for copy and paste data from opvia
    if len(raw_list) == 1:
        raw_input = raw_list[0]
        # Change to uppercase
        raw_input = raw_input.upper()
        # Remove all spaces
        raw_input = re.sub(" ", "", raw_input)
        # Split into list by comma.
        in_list = raw_input.split(",")
        hyphen_list = []

        for item in in_list:
            # Catch S/NS labels
            if item == "S":
                # Sterile label
                return ["STERILE"]

            elif item == "NS":
                # Not-Sterile label
                return ["NOT_STERILE"]

            elif "*" in item:
                hyphen_list.extend(expand_multiply(item))

            elif "-" in item and len(item) == 17:
                hyphen_list.append(item)

            elif len(item) == 8:
                hyphen_list.append(item)

            else:
                print(f"Incorrectly formatted ID: {item}")

        for hyphen_item in hyphen_list:
            if "-" in hyphen_item:
                out_list.extend(expand_hyphen(hyphen_item))
            elif len(hyphen_item) == 8:
                out_list.append(hyphen_item)
            else:
                print(f"Incorrectly formatted ID: {hyphen_item}")
    elif len(raw_list) > 1 and len(raw_list[0]) == 8:
        out_list = raw_list

    return out_list

def app_label_selection(app_input: str) -> list:
    """
    This function takes input from the webapp on the range of labels they would like to print by using the item ID, and
    returns these as a list of item ID's.
    :return list: list of item ID's for desired labels to print.
    """

    out_list = []
    raw_list = app_input.split("\n")

    # Check for copy and paste data from opvia
    if len(raw_list) == 1:
        raw_input = raw_list[0]
        # Change to uppercase
        raw_input = raw_input.upper()
        # Remove all spaces
        raw_input = re.sub(" ", "", raw_input)
        # Split into list by comma.
        in_list = raw_input.split(",")
        hyphen_list = []

        for item in in_list:
            # Catch S/NS labels
            if item == "S":
                # Sterile label
                return ["STERILE"]

            elif item == "NS":
                # Not-Sterile label
                return ["NOT_STERILE"]

            elif "*" in item:
                hyphen_list.extend(expand_multiply(item))

            elif "-" in item and len(item) == 17:
                hyphen_list.append(item)

            elif len(item) == 8:
                hyphen_list.append(item)

            else:
                print(f"Incorrectly formatted ID: {item}")

        for hyphen_item in hyphen_list:
            if "-" in hyphen_item:
                out_list.extend(expand_hyphen(hyphen_item))
            elif len(hyphen_item) == 8:
                out_list.append(hyphen_item)
            else:
                print(f"Incorrectly formatted ID: {hyphen_item}")
    elif len(raw_list) > 1 and len(raw_list[0]) == 8:
        out_list = raw_list

    return out_list

def table_lookup(id_list: list) -> str:
    """
    This function looks up and returns the correct table ID based on the ID type of the first ID in the entered id list.
    :param id_list: list of ID's as returned by user_label_selection.
    :return: table id string to pull table from Opvia.
    """
    table_id_dict = {
        "I": "57a88abe-ef33-4544-9d02-d1e08232c3fb",
        "V": "aa84eabd-5c5d-42d7-bf59-80fffc7fec8e",
        "C": "fad34b0e-9d3f-48f2-9e4e-0f42e5b12ada",
        "E": "70044410-ab38-4123-93d3-7731777db882",
        "M": "ec0f4673-e504-4ea0-b58e-751ef8e3b726"
    }
    # Get the uppercase id character to pass into the dict.
    id_slice = id_list[0][0].upper()

    # Try returning the table_id, excepting key errors.
    try:
        return table_id_dict[id_slice]
    except KeyError:
        print("Unrecognised ID type, please check your input.")
        return ""


# If:thirsty{make peppermint tea} - Will


def get_table_data(table_id: str) -> pd.DataFrame:
    """
    This function takes the table ID as an input and returns the downloaded table from Opvia in a pandas dataframe
    object.
    :param table_id: The table ID for the table to download.
    :return pd.DataFrame: the dataframe containing the data from the opvia table.
    """
    # Initialise connection and log in to Opvia.
    email = get_username()
    password = get_password()

    opvia_base_url = "https://api.opvia.org"

    prod_config = {
        "apiKey": "AIzaSyCc2cHHpMRvHkKbeD4t-BtWqq3Cd-f-SD0",
        "authDomain": "opvia-app.firebaseapp.com",
        "databaseURL": "https://opvia-app-default-rtdb.europe-west1.firebasedatabase.app",
        "projectId": "opvia-app",
        "storageBucket": "opvia-app.appspot.com",
        "messagingSenderId": "1073413948009",
        "appId": "1:1073413948009:web:3b75182a71a62e174918f8",
    }

    firebase = pyrebase.initialize_app(prod_config)
    auth = firebase.auth()

    base_user = auth.sign_in_with_email_and_password(email, password)

    print(f"Signing in as {base_user.get('displayName') or base_user.get('email')}")

    base_token = base_user["idToken"]
    base_auth_header = {"Authorization": f"Bearer {base_token}"}

    token_upgrade_endpoint = f"{opvia_base_url}/auth/login"
    res = requests.post(token_upgrade_endpoint, headers=base_auth_header)
    custom_token = res.json()["token"]

    user = auth.sign_in_with_custom_token(custom_token)
    opvia_token = user["idToken"]
    auth_header = {"Authorization": f"Bearer {opvia_token}"}

    table_download_url = f"{opvia_base_url}/download/table/{table_id}"

    print("Fetching data...")

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_content = requests.get(table_download_url, headers=auth_header).content
        csv_file = os.path.join(temp_dir, "table.csv")
        with open(csv_file, "wb") as f:
            f.write(csv_content)
        df = pd.read_csv(csv_file)
    print("Data received.")

    return df


def trim_table_data(dataframe: pd.DataFrame, id_list: list) -> pd.DataFrame:
    # Need to select the right name for the ID column based on the id_list
    id_label_dict = {
        "I": "Item ID",
        "V": "Vessel ID",
        "C": "Cell Bank ID",
        "E": "Equipment ID",
        "M": "Media ID"

    }

    # Set the index based on the id label dict.
    id_slice = id_list[0][0].upper()
    id_name = id_label_dict[id_slice]

    # Logging
    print(f"{id_name} detected.")

    # Set the index of the table to the correct ID column to allow searching.
    dataframe.set_index(id_name, inplace=True, verify_integrity=False, drop=False)
    # Select and save the records that match the ID's in the id_list.
    trim_data = pd.DataFrame()
    # Iteratively, so that non-existent IDs can be caught and handled.
    for each_id in id_list:
        try:
            trim_data = pd.concat([trim_data, dataframe.loc[each_id]], axis=1)

        except KeyError:
            print(f"No item exists for ID: {each_id}")
    # Fix wrong orientation from weird concatenation
    trim_data = trim_data.transpose()
    # Replace NaN with empty string.
    trim_data.fillna("", inplace=True)

    return trim_data


def get_data_opvia_iter(id_list: list) -> list:
    """
    Gets data for each item pointed to by the ID's in the id_list parameter from Opvia and returns a list of
    dictionaries describing each item.
    :param id_list: input list consisting of a list of ID's for entities stored in Opvia. Must all be same type of item.
    :return item_dict_list: returns a list of dictionaries describing each entity from the id list input.
    """
    item_dict_list = []

    # Get table ID
    table_id = table_lookup(id_list)

    # Get table data
    data = get_table_data(table_id)

    # Trim to just what we need.
    trim_data = trim_table_data(data, id_list)

    # Convert each record into a dict with pd.
    item_dict_list = trim_data.to_dict(orient="records")

    return item_dict_list


def continuation_check() -> bool:
    """
    This function is used to check if the user wants to continue inputting ID's for printing after submitting one
    already.
    """

    user_input = input("Do you wish to print more? [Y]es / [N]o \n").lower()

    if user_input == ("y" or "yes" or "es" or "ye"):
        return True
    elif user_input == ("n" or "no" or "o"):
        return False
    else:
        return False


def local_print_driver() -> None:
    """
    Driver code to initiate local printing tool.
    """
    # Continuation flag
    cont = True
    while cont:
        # Take input for requested labels. If invalid ID and list is empty, restart.
        id_list = user_label_selection()
        if not bool(id_list):
            local_print_driver()
        # If sterile/not-sterile labels, print them
        if id_list[0] == "STERILE":
            with tempfile.NamedTemporaryFile(suffix=".zpl") as label:
                zebra_ftp_print(sterile_label_gen(label), "S/NS")
        elif id_list[0] == "NOT_STERILE":
            with tempfile.NamedTemporaryFile(suffix=".zpl") as label:
                zebra_ftp_print(not_sterile_label_gen(label), "S/NS")
        else:
            # Pull down data for requested labels
            item_dict_list = get_data_opvia_iter(id_list)

            # generate labels and print immediately
            for item in item_dict_list:
                print("Printing label...")
                # check for timeout error and prompt user to change networks.
                try:
                    master_print(item, id_list[0][0])
                except TimeoutError:
                    print("Could not connect to printer, please check you are connected to the Extracellular WiFi network.")

        print("Job done.")

        # Ask user if they want to continue
        cont = continuation_check()

def app_print_driver(app_input: str) -> None:
    """
    Print driver for app input
    :return:
    """
    # Take input for requested labels. If invalid ID and list is empty, restart.
    id_list = app_label_selection(app_input)
    if not bool(id_list):
        print("No valid input, stopping.")
    # If sterile/not-sterile labels, print them
    if id_list[0] == "STERILE":
        with tempfile.NamedTemporaryFile(suffix=".zpl") as label:
            zebra_ftp_print(sterile_label_gen(label), "S/NS")
    elif id_list[0] == "NOT_STERILE":
        with tempfile.NamedTemporaryFile(suffix=".zpl") as label:
            zebra_ftp_print(not_sterile_label_gen(label), "S/NS")
    else:
        # Pull down data for requested labels
        item_dict_list = get_data_opvia_iter(id_list)

        # generate labels and print immediately
        for item in item_dict_list:
            print("Printing label...")
            # check for timeout error and prompt user to change networks.
            try:
                master_print(item, id_list[0][0])
            except TimeoutError:
                print("Could not connect to printer, please check you are connected to the Extracellular WiFi network.")

        print("Job done.")


import tempfile


### LABEL GENERATORS ###


def generic_small_label_component(label: tempfile.NamedTemporaryFile) -> None:
    """Writes the generic components of the label: The bounding box, the logo and the date (dd/MMM/yyyy) to the
    NamedTemporaryFile object passed as an argument."""
    # Write label setup section, dotted box and logo.
    label.write(
        """^FX --label setup--
CT~~CD,~CC^~CT~
^XA
^PW229
^FX --logo--
^FO160,96^GFA,00512,00512,00008,:Z64:
eJzNzTEOwyAMheFXMTBygUhcI1O4VodKJDfjKD4CY4YIN35mzljVyz/gDwP/N0Hibo2SmjX1zGYpbJHK1qbc00MtLw2DfMSL/Eone+a+WnuRD7+tzRZD02M8wXRD3r3hw11MjskxOd7OFzjf4Lyg7rPwbvD3Bb7/w/kCvHs/BA==:F21B

^FX --dotted box--
^FO0,0^GFA,05120,05120,00032,:Z64:
eJzt2LEJACAQBEENBBu0H0vXBgThEJNZMJzH+Er5XBunrnh997P49Nyv8zzP8zzP8zzP8zzPP/ZBV/tHPJKE+4+yFu0lNDk=:585E
""".encode(
            "utf-8"
        )
    )

    # Write date printed section.
    label.write(
        """
^FX --date--
^SLT,1
^FT72,132
^A0I,14,14
^FC%,{,#
^FD%d/%b/%Y^FS
        """.encode(
            "utf-8"
        )
    )

    return None


def generic_thin_label_component(label: tempfile.NamedTemporaryFile) -> None:
    """
    Writes the generic components of the vessel label: the logo to the NamedTemporaryFile object passed as an argument.
    """

    label.write("""
    CT~~CD,~CC^~CT~
^XA

^FX --- logo graphic ---
^FO512,0^GFA,00512,00512,00008,:Z64:eJzVzrENwCAMRFEjFynZIIzCSmwAbMYoGSElBcLBh+t0KULBR4InQ/TR8uVEQ4lobBnNRVCpqBOeWp7H0B7Dd/AebvA7XuiVmx5Ck6oXoQrrQ79gf4NxQcxtUl7msnE2zsad8USbd7e/P9y0jl0CX3ui/f4f6wH/cULH:53E1
""".encode(
        "utf-8"
    ))

    return None


def generic_large_label_component(label: tempfile.NamedTemporaryFile) -> None:
    """Writes generic components for the Large label. Including dotted box, logo and date."""
    # Write label setup section, dotted box and logo, at correct scale for large label.
    label.write(
        """^FX --label setup--
CT~~CD,~CC^~CT~
^XA
^MMT

^FX --logo--
^FO10,461^GFA,165,296,8,:Z64:eJyV0LENgCAQBdBTCspbwOTWsNLFSNDNGIURKCkImPtcpZUUvIRw/wcCzdU/Mgwkl7qTJBwUycpSpcDGFXbf4HAzYtwDxjQQcOYIpZzqxhXBh2+sRtdXXP+OJRtDL1uvt173s5esVwNoBswHL+8fCOaO/QFVaz70:755B

^FX --dotted box--
^FO4,4^GFA,169,20000,40,:Z64:eJzt3LEVABAQRMF7ImUrRaxKOnCBBPPjfVPClrGvRUSNfZnNa7VjIx6Px+PxeDwej8fj8Xg8Ho/H4/F4PB6Px+PxeDwej8fj8Xg8Ho/H4/F4PB6Px+PxeDwej8fj8Xg8Ho/H4/F4PB7vfu+3sj9tJfH71tduAgFvIdA=:DC21""".encode(
            "utf-8")
    )

    return None


def end_label(label: tempfile.NamedTemporaryFile) -> None:
    """Takes label TextIOWrapper object as arg and adds the end label section, returning none.
    :param tempfile.NamedTemporaryFile() label: The label object to write the ending section to."""
    # Write end label section and specify print quantity.
    label.write(
        """
^FX --specify label amount and end label def.--
^PQ1,0,1,Y
^XZ
""".encode(
            "utf-8"
        )
    )
    return None


def item_label_gen(
        active_label: tempfile.NamedTemporaryFile,
        item_dict: dict
) -> tempfile.NamedTemporaryFile():
    """
    Generates and returns a .zpl text file based on the given parameters that can be sent to a zebra printer to print an
     item label. exp_date is formatted into a dd/MMM/YYYY format, using reformat_opvia_date function.
    """
    # Get variables to print. Names must be exactly as in Opvia.
    item_id = item_dict["Item ID"]
    raw_exp_date = item_dict["Expiration date"]
    # Append note to mat name, so it is shown on label. for notes, etc.
    mat_name = item_dict["Material Name"] + "-" + item_dict["Label Note"]
    conc = item_dict["Concentration"]
    lot_no = item_dict["Lot No"]
    if item_dict["Project ID Overwrite"] != "":
        project_id = item_dict["Project ID Overwrite"]
    else:
        project_id = item_dict["Project ID"]

    # Format the date.
    format_exp_date = reformat_opvia_date(raw_exp_date)

    # Write generic label components: dotted box, logo and date printed.
    generic_small_label_component(active_label)

    # Write Item ID barcode section.
    active_label.write(
        f"""
^FX --barcode---
^BY72,72^FT80,8^BXI,6,200,0,0,1,~
^FH\\^FD{item_id}^FS
""".encode(
            "utf-8"
        )
    )

    # Write text field section, including formatted expiry date.
    active_label.write(
        f"""
^FX --text fields--
^FT183,122^A0I,23,24^FH\\^FDItem^FS
^FT221,88^A0I,25,24^FH\\^FD{mat_name}^FS
^FT223,53^A0I,23,24^FH\\^FDLot:^FS
^FT179,53^A0I,23,24^FH\\^FD{lot_no}^FS
^FT223,32^A0I,23,24^FH\\^FDConc:^FS
^FT167,32^A0I,23,24^FH\\^FD{conc}^FS
^FT223,10^A0I,23,18^FH\\^FDExp:^FS
^FT190,10^A0I,23,20^FH\\^FD{format_exp_date}^FS
^FT124,122^A0I,23,24^FH\\^FD{project_id}^FS
""".encode(
            "utf-8"
        )
    )

    end_label(active_label)

    return active_label


def equipment_label_gen(
        active_label: tempfile.NamedTemporaryFile,
        item_dict: dict
) -> tempfile.NamedTemporaryFile:
    """
    Writes an equipment label based on the item_dict passed in, to the tempfile also passed in.
    """
    equipment_id = item_dict["Equipment ID"]
    equipment_name = item_dict["Name"]

    # Write generic large label components
    generic_large_label_component(active_label)

    # Write ID barcode
    active_label.write(
        f"""
^FT284,156^BXB,11,200,0,0,1,_,1
^FH\\^FD{equipment_id}^FS""".encode("utf-8")
    )

    # Write Equipment name, and equipment tag by logo.
    active_label.write(
        f"""
^FT35,458^A0B,23,25^FH\^CI28^FDEquipment^FS^CI27
^FT93,492^A0B,45,48^FH\\^CI28^FD{equipment_name}^FS^CI27""".encode(
            "utf-8"
        )
    )

    # End label
    end_label(active_label)

    return active_label


def cellbank_label_gen(
        active_label: tempfile.NamedTemporaryFile, item_dict: dict
) -> tempfile.NamedTemporaryFile:
    """
    Generates and returns a .zpl text file based on the given parameters that can be sent to a zebra printer to print a
    cell bank label. Storage date is reformatted into a dd/MMM/YYYY format, using reformat_opvia_date function.
    """

    cell_bank_id = item_dict["Cell Bank ID"]
    cell_name = item_dict["Cell Type"]
    conc = item_dict["Concentration (cells/ml)"]
    raw_store_date = item_dict["Storage Date"]
    # Handle empty passage numbers
    try:
        passage_no = str(int(item_dict["Passage"]))
    except ValueError:
        passage_no = ""

    # Format date
    format_store_date = reformat_opvia_date(raw_store_date)

    # Format concentration to scientific notation. check if should be zero.
    if conc == "":
        conc = 0
    conc = "{:.2e}".format(conc)

    # Write generic label components: dotted box, logo and date printed.
    generic_small_label_component(active_label)

    # Write Cell Bank ID barcode section.
    active_label.write(
        f"""
^FX --barcode---
^BY72,72^FT80,8^BXI,6,200,0,0,1,~
^FH\\^FD{cell_bank_id}^FS
    """.encode(
            "utf-8"
        )
    )
    # Write text field section, including formatted storage date.
    active_label.write(
        f"""
^FT183,122^A0I,23,24^FH\\^FDCell bank^FS
^FT221,88^A0I,25,24^FH\\^FD{cell_name}^FS
^FT223,53^A0I,23,18^FH\\^FDCell/ml:^FS
^FT165,53^A0I,23,20^FH\\^FD{conc}^FS
^FT223,32^A0I,23,24^FH\\^FDStored:^FS
^FT223,10^A0I,23,24^FH\\^FD{format_store_date}^FS
^FT58,95^A0I,23,24^FH\\^FDP:^FS
^FT37,95^A0I,23,24^FH\\^FD{passage_no}^FS
    """.encode(
            "utf-8"
        )
    )
    # without breaking indentation.
    # active_label.write("\n".join((
    #     "\n",
    #     "^FT183,122^A0I,23,24^FH\\^FDCell bank^FS",
    #     f"^FT221,88^A0I,25,24^FH\\^FD{cell_name}^FS",
    #     "^FT223,53^A0I,23,24^FH\\^FDCell/ml:^FS",
    #     f"^FT147,53^A0I,23,24^FH\\^FD{conc}^FS",
    #     "^FT223,32^A0I,23,24^FH\\^FDStored:^FS",
    #     f"^FT223,10^A0I,23,24^FH\\^FD{format_store_date}^FS",
    #     "^FT58,95^A0I,23,24^FH\\^FDP:^FS",
    #     f"^FT37,95^A0I,23,24^FH\\^FD{passage_no}^FS")).encode(
    #     "utf-8"
    # )
    # )

    end_label(active_label)

    return active_label


def new_cellbank_label_gen(active_label: tempfile.NamedTemporaryFile,
                            item_dict: dict) -> tempfile.NamedTemporaryFile:
    """
    Writes new label layout for both internal and external use to the active label tempfile and returns it.
    this function adds all of the necessary label components itself and does not call the others. this is because
    the formatting is significantly different from the old label style.
    :param active_label: active label tempfile
    :param item_dict: dict containing record attributes
    :return: the active_label tempfile.
    """
    cell_bank_id = item_dict["Cell Bank ID"]
    name = item_dict["Cell Type"]
    species = item_dict["Species"]
    cell_morphology = item_dict["Cell Morphology"]
    catalog_number = item_dict["Catalog Number"]
    total_cells = item_dict["Total Cells"]
    volume = item_dict["Volume (mL)"]
    conc = item_dict["Concentration (cells/ml)"]

    # Fix empty numbers
    if total_cells == "":
        total_cells = 0
    if volume == "":
        volume = 0
    if conc == "":
        conc = 0
    # Format conc to sci notation
    conc = "{:.2e}".format(conc)
    total_cells_format = format_cell_number(total_cells)

    label_string = f"""
CT~~CD,~CC^~CT~
^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR4,4~SD15^JUS^LRN^CI0^XZ
^XA
^MMT
^PW229
^LL0153
^LS0
^FO160,96^GFA,00512,00512,00008,:Z64:
eJzV0L0JwCAQgFHF4poQR3CTuFY6hSxmNnGElFdIzP1YhoBlrnkgfpxozA8HXWEsQmVd8yJgED1GMVxJ7sXaM5vOLnk/bhXawt4eN7ZRwO4UmJfAUiD7KJB9FHztiyOPY1/Q3K4jL/5S9dlQQxnnWQXJXJ78npl5AHRyPKg=:890C
^FO0,96^GFA,01536,01536,00024,:Z64:
eJzt0TFuwzAMBVAFGjjyBvRFAutaGYpCgQeNvkF9FBvooLE3KFx48BgCGeJBkErJSdsM2Yqig/9EPAIERSm1Zcs/DrjO8pmJ9LIL0FmqsZlT9n7ky0KEASL0IxlofPE0cgpEVcQESbzxrvjEHGqSBrZSEzQnhdmHhWUM7bEDPywEx6vbQ3EFVnt7ILDxy/nOw52bdPOnR67TD99/z8+OeZ/VX7TsU8OxeOU+uHiNFUj9fN0zubR61aPU52imN7v6WBwjyB2maGaf/eL6oTgELXd7fTdzM4h716riO1YLtJrMSY+4/gErJe+9fYhVkH7Bc+uBb/mzfALyrK/1:C14B
^BY2,3,36^FT216,0^BCI,,N,N
^FD{cell_bank_id}^FS
^FT226,103^A@I,17,18,TT0003M_^FH\^CI17^F8^FD{species}-{cell_morphology}^FS^CI0"""\
        .replace("\n", "")\
        .encode("utf-8")

    if volume == 0 or total_cells == 0:
        label_string += f"""^FT226,82^A@I,17,18,TT0003M_^FH\^CI17^F8^FD{conc} cells in 1mL^FS^CI0"""\
            .replace("\n", "")\
            .encode("utf-8")
    else:
        label_string += f"""^FT226,82^A@I,17,18,TT0003M_^FH\^CI17^F8^FD{total_cells_format} cells in {volume}mL^FS^CI0"""\
            .replace("\n", "")\
            .encode("utf-8")

    label_string += f"""^FT224,62^A@I,17,18,TT0003M_^FH\^CI17^F8^FDCat:^FS^CI0
^FT191,62^A@I,17,18,TT0003M_^FH\^CI17^F8^FD{catalog_number}^FS^CI0
^FT169,39^A@I,17,18,TT0003M_^FH\^CI17^F8^FD{cell_bank_id}^FS^CI0
^PQ1,0,1,Y^XZ
"""\
        .replace("\n", "")\
        .encode("utf-8")

    return active_label.write(label_string)


def vessel_label_gen(active_label: tempfile.NamedTemporaryFile,
                     item_dict: dict
                     ) -> tempfile.NamedTemporaryFile:
    """
    Writes the vessel label details to the passed in file and returns it.
    :param active_label: tempfile.NamedTemporaryFile The file to write to.
    :param item_dict: dict containing the entity information.
    :return: active label with vessel info written to it.
    """
    # Get data
    vessel_id = item_dict["Vessel ID"]

    # Write generic thin label components
    generic_thin_label_component(active_label)

    # Write specific vessel label components, the Vessel text and Barcode.
    active_label.write(f"""
^FT508,16^A0I,28,28^FH\^FDVessel^FS

^BY2,3,37^FT334,19^BCI,,Y,N
^FD{vessel_id}^FS""".encode("utf-8"))

    end_label(active_label)

    return active_label
def small_vessel_label_gen(active_label: tempfile.NamedTemporaryFile, item_dict: dict) -> tempfile.NamedTemporaryFile:
    """
    Writes the vessel label details to the passed in file and returns it.
    In the format of a "small" label instead of a thin plate label.
    :param active_label:
    :param item_dict:
    :return:
    """
    # Get data
    vessel_id = item_dict["Vessel ID"]

    generic_small_label_component(active_label)

    # Write vessel label fields
    active_label.write(f"""
^FX --barcode---
^BY72,72^FT80,8^BXI,6,200,0,0,1,~
^FH\\^FD{vessel_id}^FS

^FX --text fields--
^FT183,122^A0I,23,24^FH\\^FDVessel^FS
""".encode("utf-8"))

    # End label
    end_label(active_label)

    return active_label

def media_label_gen(active_label: tempfile.NamedTemporaryFile, item_dict: dict) -> tempfile.NamedTemporaryFile:
    """Generates and returns a .zpl text file based on the given item_dict, to be sent to a label printer to be printed."""

    comp_list = item_dict["Media Composition"]
    # We need to turn comp list from a string that looks like a list into an actual list
    fix_comp_list = re.sub('\[|\]|"', "", comp_list).split(",")

    formulation_name = item_dict["Formulation Name"]
    expiry_date = reformat_opvia_date(item_dict["Expiry Date"])
    project_id = item_dict["Project ID"]
    media_id = item_dict["Media ID"]
    format_comp_list = get_media_composition(fix_comp_list)
    # pad with empty lines
    while len(format_comp_list) < 9:
        format_comp_list.append("")

    # Logo is included here as line 2. no dotted box.
    active_label.write(f"""
^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR4,4~SD20^JUS^LRN^CI0^XZ
^XA
^MMT
^PW305
^LL0508
^LS0
^FO256,0^GFA,00512,00512,00008,:Z64:
eJzN0LENgCAQBVAIBSUb6Bp2rOQAJspmjsIIV1IQUO4+FlqZWHgFr4H/cyj19UxwgQXW7tZOHde9achHNo3EZpfYYjPfq0YCapCAdZcAj4ARAQ4B9hnAbjU0zfksoXd+2avQq9DLOhpYS7K5Idlcx2vzu/1n/jAH2fNCzA==:22E6
^FT270,50^A@R,23,22,TT0003M_^FH\\^CI17^F8^FDMedia^FS^CI0
^FT272,304^A@R,23,22,TT0003M_^FH\\^CI17^F8^FDExpires:^FS^CI0
^FT270,146^A@R,23,22,TT0003M_^FH\\^CI17^F8^FDProject:^FS^CI0
^FT236,9^A@R,28,29,TT0003M_^FH\\^CI17^F8^FD{formulation_name}^FS^CI0
^FT272,384^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{expiry_date}^FS^CI0
^FT270,225^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{project_id}^FS^CI0
^FT204,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[0]}^FS^CI0
^FT182,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[1]}^FS^CI0
^FT160,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[2]}^FS^CI0
^FT137,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[3]}^FS^CI0
^FT115,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[4]}^FS^CI0
^FT93,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[5]}^FS^CI0
^FT71,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[6]}^FS^CI0
^FT49,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[7]}^FS^CI0
^FT27,10^A@R,23,22,TT0003M_^FH\\^CI17^F8^FD{format_comp_list[8]}^FS^CI0
""".encode("utf-8"))

    # Write barcode
    active_label.write(f"""
^BY132,132^FT15,357
^BXR,11,200,0,0,1,~
^FH\^FD{media_id}^FS""".encode("utf-8"))

    end_label(active_label)

    return active_label


def sterile_label_gen(active_label: tempfile.NamedTemporaryFile) -> tempfile.NamedTemporaryFile:
    """
    Creates a Sterile label.
    :param active_label: the active temporary file label to write the label data to.
    :return: the active label with label data.
    """
    generic_small_label_component(active_label)

    active_label.write("""
^FT183,122^A0I,23,25^FH\^CI28^FDS/NS^FS^CI27
^FT218,40^A0I,76,76^FH\^CI28^FDSterile^FS^CI27
""".encode("utf-8"))

    end_label(active_label)
    return active_label

def not_sterile_label_gen(active_label: tempfile.NamedTemporaryFile) -> tempfile.NamedTemporaryFile:
    """
    Creates a Not-Sterile label.
    :param active_label: active_label: the active temporary file label to write the label data to.
    :return: the active label with label data.
    """
    generic_small_label_component(active_label)

    active_label.write("""
^FT183,122^A0I,23,25^FH\^CI28^FDS/NS^FS^CI27
^FT218,40^A0I,81,48^FH\^CI28^FDNot Sterile^FS^CI27
""".encode("utf-8"))

    end_label(active_label)

    return active_label

### OPVIA TOOLS ###

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


def label_size_selection(id_char: str) -> str:
    """
    Takes the ID char of the label as an input and then returns the correct IP address for the printer with the right
    size labels.
    """
    # 10.1.213.52 is small labels - including modified vessel currently
    # 10.1.213.54 is large labels
    # 10.1.213.55 is thin labels (vessel) not yet.

    ip_dict = {
        "I": "10.1.213.52",
        "C": "10.1.213.52",
        "S/NS": "10.1.213.52",
        "E": "10.1.213.54",
        "V": "10.1.213.52",
        "M": "10.1.213.54"
    }

    return ip_dict[id_char]


def get_media_composition(comp_list: list) -> list:
    """
    takes a list of compositions of a media and returns a list of strings containing the
    component name and concentration.
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
        if comp_dict["Percent Concentration"] == "":
            comp_string_list.append(
                re.sub("μ", "u", comp_dict["Concentration Comment"]) + " " + str(comp_dict["Description"])
            )
        else:
            comp_string_list.append(
                str(comp_dict["Percent Concentration"] * 100) + "% " + str(comp_dict["Description"])
            )

    return comp_string_list


### PRINT TOOLS ###


def zebra_ftp_print(in_label: tempfile.NamedTemporaryFile, id_char: str) -> None:
    """
    Takes a label temp file and the id_char as an argument. Selects the correct printer for the label size and
     sends the file over FTP.
    :param in_label tempfile.NamedTemporaryFile: The label io.TextIOWrapper object to print the label of.
    :param id_char str: The ID of the entity type to be printed.
     """

    # Select correct IP address for correct label size
    printer = label_size_selection(id_char)

    # Establish connection and login.
    try:
        ftp_print = FTP(printer)
    except TimeoutError:
        print("Could not connect to printer, please check you are connected to the Extracellular WiFi network.")
        return None

    ftp_print.login()

    # File name is acquired using os.path. This is for display purposes only, actual filename does not matter.
    label_path = in_label.name
    # Reset the pointer to start of file, so it can be read and printed.
    in_label.seek(0)
    ftp_print.storbinary(f"STOR {path.basename(label_path)}", in_label)

    # End FTP session
    ftp_print.close()

    return None


def master_print(record_dict: dict, id_char: str) -> None:
    """Master print handler to be called from Opvia and results in printing of the correct label for the type of record
    object passed in. Creates temporary file, generates label, then sends to printer."""

    # Create temp file to store label.
    with tempfile.NamedTemporaryFile(suffix=".zpl") as label:
        # populate label
        generic_label_handler(label, record_dict, id_char)
        # Print label
        # Debug: print label to stdout
        label.seek(0)
        print(label.read())
        #zebra_ftp_print(label, id_char)

    return None


def generic_label_handler(label_file, record_dict: dict, id_char: str) -> TextIOWrapper:
    """Generic label handler to print any type of label from Opvia. Takes the record of the item as an input, decides
    what kind of label to print and then calls the relevant label generation function."""
    # Takes the first character of the ID and uses to find correct generator from dict.

    # I = Item, P = Plate, C = Cellbank, E = Equipment
    label_gen_dict = {
        "I": item_label_gen,
        "V": small_vessel_label_gen,
        "C": new_cellbank_label_gen,
        "E": equipment_label_gen,
        "M": media_label_gen
    }

    label = label_gen_dict[id_char](label_file, record_dict)

    return label