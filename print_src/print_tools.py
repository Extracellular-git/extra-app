#!/usr/bin/env python3
import io
import os
import tempfile
from ftplib import FTP
from os import path
import label_generators

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
        "V": "10.1.213.52"
    }

    return ip_dict[id_char]


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
        # label.seek(0)
        # print(label.read())
        zebra_ftp_print(label, id_char)

    return None


def generic_label_handler(label_file, record_dict: dict, id_char: str) -> TextIOWrapper:
    """Generic label handler to print any type of label from Opvia. Takes the record of the item as an input, decides
    what kind of label to print and then calls the relevant label generation function."""
    # Takes the first character of the ID and uses to find correct generator from dict.

    # I = Item, P = Plate, C = Cellbank, E = Equipment
    label_gen_dict = {
        "I": label_generators.item_label_gen,
        "V": label_generators.small_vessel_label_gen,
        "C": label_generators.new_cellbank_label_gen,
        "E": label_generators.equipment_label_gen
    }

    label = label_gen_dict[id_char](label_file, record_dict)

    return label