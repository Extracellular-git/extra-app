#!/usr/bin/env python3
import io
import tempfile

from opvia_tools import reformat_opvia_date, format_cell_number, get_media_composition

##############################
## Generic label components ##
##############################

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


##################
## Small labels ##
##################


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
^FD>:CB>5100035^FS
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


##################
## Large labels ##
##################


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


def media_label_gen(active_label: tempfile.NamedTemporaryFile, item_dict: dict) -> tempfile.NamedTemporaryFile:
    """Generates and returns a .zpl text file based on the given item_dict, to be sent to a label printer to be printed."""

    formulation_name = item_dict["Formulation Name"]
    expiry_date = reformat_opvia_date(item_dict["Expiry Date"])
    project_id = item_dict["Project ID"]
    media_id = item_dict["Media ID"]
    comp_list = get_media_composition(item_dict["Media Composition"])
    # pad with empty lines
    while len(comp_list) < 8:
        comp_list.append("")
    # Logo is included here as line 2. no dotted box.
    active_label.write(f"""
^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR4,4~SD10^JUS^LRN^CI0^XZ
^FO256,0^GFA,00512,00512,00008,:Z64:eJzN0LENgCAQBVAIBSUb6Bp2rOQAJspmjsIIV1IQUO4+FlqZWHgFr4H/cyj19UxwgQXW7tZOHde9achHNo3EZpfYYjPfq0YCapCAdZcAj4ARAQ4B9hnAbjU0zfksoXd+2avQq9DLOhpYS7K5Idlcx2vzu/1n/jAH2fNCzA==:22E6
^MMT
^PW305
^LL0508
^LS0
^FT270,50^A@R,23,22,TT0003M_^FH\^CI17^F8^FDMedia^FS^CI0
^FT272,304^A@R,23,22,TT0003M_^FH\^CI17^F8^FDExpires:^FS^CI0
^FT270,146^A@R,23,22,TT0003M_^FH\^CI17^F8^FDProject:^FS^CI0
^FT236,9^A@R,25,24,TT0003M_^FH\^CI17^F8^FD{formulation_name}^FS^CI0
^FT272,384^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{expiry_date}^FS^CI0
^FT270,225^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{project_id}^FS^CI0
^FT204,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[0]}^FS^CI0
^FT182,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[1]}^FS^CI0
^FT160,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[2]}^FS^CI0
^FT137,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[3]}^FS^CI0
^FT115,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[4]}^FS^CI0
^FT93,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[5]}^FS^CI0
^FT71,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[6]}^FS^CI0
^FT49,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[7]}^FS^CI0
^FT27,10^A@R,23,22,TT0003M_^FH\^CI17^F8^FD{comp_list[8]}^FS^CI0
""".encode("utf-8"))

    # Write barcode
    active_label.write(f"""
^BY132,132^FT15,357
^BXR,11,200,0,0,1,~
^FH\^FD{media_id}^FS""".encode("utf-8"))

    end_label(active_label)

    return active_label
