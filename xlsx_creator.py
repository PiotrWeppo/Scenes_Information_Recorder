import pandas as pd
from files_operations import list_of_pictures


def create_dataframe(final_dict):
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


def create_xlsx_file(dataframe, video):
    video_name = video.split(".")[0]
    images = list_of_pictures("temp/thumbnails")
    writer = pd.ExcelWriter(f"{video_name}.xlsx", engine="xlsxwriter")
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
    worksheet.set_column_pixels(first_col=1, last_col=1, width=1920*0.2)
    for index in range(dataframe_length):
        worksheet.set_row_pixels(row=pic_row-1, height=1080*0.2)
        if dataframe.iloc[index]["TEXT"].startswith("VFX"):
            worksheet.embed_image(f"B{pic_row}", images[pic_index])
            pic_index += 1
        pic_row += 1

    # adjust the column widths based on the content
    # for column in DataFrame:
    #     column_length = max(DataFrame[column].astype(str).map(len).max(), len(column))
    #     col_idx = DataFrame.columns.get_loc(column)
    #     writer.sheets['sheetName'].set_column(col_idx, col_idx, column_length)
    worksheet.autofit()
    writer.close()