"""This module contains functions to create an Excel file from a dictionary."""

import os
import pandas as pd
from files_operations import (
    create_folder,
    copy_picture_from_to_folder,
)


def create_dataframe(final_dict: dict) -> pd.DataFrame:
    """Create a pandas DataFrame from a dictionary.

    Args:
        final_dict (dict): Dictionary with the final data.

    Returns:
        pd.DataFrame: DataFrame with the final data.
    """
    df = pd.DataFrame(final_dict).T
    df.reset_index(inplace=True)
    df.rename(columns={"index": "FRAME IN"}, inplace=True)
    column_order = [
        "TEXT",
        "THUMBNAIL",
        "FRAME IN",
        "FRAME OUT",
        "TC IN",
        "TC OUT",
        "REAL TC IN",
        "REAL TC OUT",
    ]
    df = df.reindex(columns=column_order)
    return df


def create_xlsx_file(
    dataframe: pd.DataFrame,
    video_path: str,
    file_save_dir: str,
    save_hq_pics: bool,
) -> None:
    """Create an Excel file from a DataFrame. Insert pictures in the Excel file.

    Args:
        dataframe (pd.DataFrame): DataFrame with the final data.
        video (str): Video name.
    """
    print("\n-Creating Excel file-")
    full_file_name = os.path.basename(video_path).split("/")[-1]
    video_title = full_file_name.split(".")[0]
    save_file_path = os.path.join(file_save_dir, f"{video_title}.xlsx")
    writer = pd.ExcelWriter(save_file_path, engine="xlsxwriter")
    dataframe.to_excel(writer, sheet_name="Sheet1", index=False)
    # dataframe.style.set_properties(**{"text-align": "center"})
    workbook = writer.book
    # cell_format = workbook.add_format()
    # cell_format.set_align("vcenter")
    worksheet = writer.sheets["Sheet1"]
    my_format = workbook.add_format()
    my_format.set_align("center")
    my_format.set_align("vcenter")
    worksheet.set_column("A:XFD", None, my_format)
    # worksheet.set_column(first_col=0, last_col=10, cell_format=cell_format)
    pic_index = 0
    pic_row = 2
    dataframe_length = len(dataframe.index)
    worksheet.set_column_pixels(first_col=1, last_col=1, width=1920 * 0.25)
    if save_hq_pics:
        create_folder(f"{file_save_dir}/'{full_file_name}' VFX Pictures")
    for index in range(dataframe_length):
        worksheet.set_row_pixels(row=pic_row - 1, height=1080 * 0.25)
        if dataframe.iloc[index]["TEXT"].startswith("VFX"):
            worksheet.insert_image(
                f"B{pic_row}",
                f"{file_save_dir}/temp/thumbnails/{dataframe.iloc[index]['FRAME IN']}.png",
            )
            if save_hq_pics:
                source_path = (
                    f"{file_save_dir}/temp/first_last_scene_frames/{dataframe.iloc[index]['FRAME IN']}.png"
                )
                destination_path = (
                    f"{file_save_dir}/'{full_file_name}' VFX"
                    f" Pictures/{dataframe.iloc[index]['FRAME IN']}.png"
                )
                copy_picture_from_to_folder(source_path, destination_path)
        pic_row += 1

    worksheet.autofit()
    print(f"Excel file '{video_title}.xlsx' created.")
    writer.close()
