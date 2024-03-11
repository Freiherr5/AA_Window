import pandas as pd
import numpy as np


# __main__ methods
# ______________________________________________________________________________________________________________________
def get_aa_window(window_size: int, aa_seq: str, aa_position: int, start_pos: bool):
    """
    generates window-slices of the sequence

    Parameters
    __________
    window_size : sets the slice of the window on each side of the position: e.g.: window size 4 = LLLL | KKKK
    aa_seq : amino acid sequence
    aa_position : position where the cut occurs

    Returns
    _______
    window of set window_size left and right of the slicing position
    """
    if __name__ == 'AA_window':
        start = aa_position - window_size - 1
        stop = aa_position + window_size - 1
        if start_pos is False:
            start = start + 1
            stop = stop + 1
        aa_window_part_left, aa_window_part_right = aa_seq[start: start + window_size], aa_seq[stop - window_size: stop]
        return aa_window_part_left, aa_window_part_right


def get_aa_window_labels(window_size: int, aa_seq: str, name_label: str, tmd_jmd_intersect: int, start_pos: bool,
                         column_pos_in_seq: str = "pos_in_seq", more_columns: dict = None):
    """
    Generates positive and negative labels

    Parameters
    __________
    window size : sets the slice of the window on each side of the position: e.g.: window size 4 = LLLL | KKKK
    aa_seq : amino acid sequence
    name_label : e.g. protein-name
    tmd_jmd_intersect : start or stop position for membrane domain sequence of a protein (can be used generally)
    start_pos : is it the first amino acid of the sequence segment or the last amino acid?
    *args_columns : add more columns to dataframe

    Returns
    _______
    df_list_labels : pd.DataFrame with labels of a specific protein
    """

    if __name__ == 'AA_window':
        columns_window = ["ID", "window_left", "window_right", "label", column_pos_in_seq]
        if more_columns is not None:
            columns_window.extend(list(more_columns.keys()))

        # generate positive-label
        window_seq = get_aa_window(window_size, aa_seq=aa_seq, aa_position=tmd_jmd_intersect, start_pos=start_pos)
        list_labels = [[f"{name_label}__0", window_seq[0], window_seq[1], 1, tmd_jmd_intersect]]
        if more_columns is not None:
            list_labels.extend(list(more_columns.values()))

        # generate negative N/C-term label
        i = 1
        while i < window_size:
            left_shift_window_seq = get_aa_window(window_size, aa_seq=aa_seq, aa_position=tmd_jmd_intersect - i,
                                                  start_pos=start_pos)
            right_shift_window_seq = get_aa_window(window_size, aa_seq=aa_seq, aa_position=tmd_jmd_intersect + i,
                                                   start_pos=start_pos)
            sublist = [
                [f"{name_label}__-{i}", left_shift_window_seq[0], left_shift_window_seq[1], 0, tmd_jmd_intersect - i],
                [f"{name_label}__{i}", right_shift_window_seq[0], right_shift_window_seq[1], 0, tmd_jmd_intersect + i]]
            if more_columns is not None:
                sublist.extend(list(more_columns.values()))
            list_labels.extend(sublist)
            i += 1
        df_list_labels = pd.DataFrame(list_labels, columns=columns_window)
        return df_list_labels


def label_describe(df):
    """
    purely an attribute for get_aa_window_df() and modify_label_by_ident_column() --> how many positive labels?

    Parameters
    __________
    df : label_df(_modified)

    Returns
    _______
    df_label_describe : pd.DataFrame.describe() method applied slice wise on original label_df
    """
    if __name__ == 'AA_window':
        df_label_search_list = list(dict.fromkeys([str(index).split("__")[0] for index in df.index.tolist()]))

        list_describe = []
        for query in df_label_search_list:
            df_slice = df.reset_index()[df.reset_index()["ID"].str.contains(query)]
            arr_slice_positives = np.array([str(id_tag).split("__")[0] for id_tag in df_slice["ID"].tolist()])
            filter_list_slice_label = np.where(arr_slice_positives == query)
            df_slice = df_slice.iloc[filter_list_slice_label]

            row, column = df_slice.shape
            count_positives = df_slice["label"].to_numpy().tolist().count(1)
            percent_positives = f"{count_positives} / {row}"
            list_describe.append([query, count_positives, percent_positives])
        label_wise_columns = ["ID", "positive_count", "positive_percent"]
        df_label_wise = pd.DataFrame(list_describe, columns=label_wise_columns)

        describe_all_labels_columns = ["average_positive", "min", "max", "ID_count"]
        labels_pos = df_label_wise["positive_count"].to_numpy().tolist()
        list_describe_all_labels = [f"{round(np.mean(labels_pos), 2)} / {row}", f"{np.min(labels_pos)} / {row}",
                                    f"{np.max(labels_pos)} / {row}", f"{len(df_label_search_list)}"]
        df_label_describe = pd.Series(list_describe_all_labels).set_axis(describe_all_labels_columns)
        return df_label_wise, df_label_describe
# ______________________________________________________________________________________________________________________


def get_aa_window_df(window_size: int, df, column_id: str, column_seq: str, column_aa_position: str,
                     start_pos: bool = True, column_pos_in_seq: str = None, more_columns_from_df: list = None):
    """
    Parameters
    __________
    window_size = defines AA_window that is shifted --> given size is mirrored for N and C term
    df : pd.DataFrame
    column_id : column name of sequence ID e.g. UniProt entry
    column_seq : column name with the full AA_seq
    column_aa_position : column name with the TMD/JMD intersection within the AA (-1 since count from 1, not from 0)
    more_columns_from_df : add more columns for further processing

    Returns
    _______
    df with the sequence windows of positive label and negative labels
    """

    aa_window_labeled_sub_df = None

    list_id = df[column_id].to_numpy().tolist()
    list_seq = df[column_seq].to_numpy().tolist()
    list_position = df[column_aa_position].to_numpy().tolist()

    list_aa_window_labeled = []
    if column_pos_in_seq is None:
        column_pos_in_seq = column_aa_position
    for id_tag, seq, pos in zip(list_id, list_seq, list_position):
        more_columns_entry = None
        # prevent NaN values from crashing the program
        if isinstance(id_tag, (str, int)) and isinstance(seq, str) and isinstance(pos, (int, float)):
            if more_columns_from_df is not None:
                dict_more_columns = {}
                for key_columns_entries in more_columns_from_df:
                    dict_more_columns[key_columns_entries] = df.set_index(column_id).loc(id_tag,
                                                                                         key_columns_entries)
                more_columns_entry = dict_more_columns
            aa_window_labeled_sub_df = get_aa_window_labels(window_size=window_size, aa_seq=seq, name_label=id_tag,
                                                            tmd_jmd_intersect=int(pos), start_pos=start_pos,
                                                            more_columns=more_columns_entry,
                                                            column_pos_in_seq=column_pos_in_seq)
            aa_window_labeled = aa_window_labeled_sub_df.to_numpy().tolist()
            list_aa_window_labeled.extend(aa_window_labeled)

    if aa_window_labeled_sub_df is not None:
        column_name = aa_window_labeled_sub_df.columns
        df_aa_window_labeled = pd.DataFrame(list_aa_window_labeled, columns=column_name).set_index(column_name[0])
    else:
        raise ValueError(f"An error has occurred, please check if the correct types have been inputted.")

    # describing attribute for df_aa_window_labeled
    get_aa_window_df.describe = label_describe(df_aa_window_labeled)[1]
    return df_aa_window_labeled


def modify_label_by_ident_column(df_label: pd.DataFrame, df_compare: pd.DataFrame, column_id: str,
                                 threshold: int = 2):
    """
    Algorithm for changing labels, only for prior multi-annotation of protein sequences!
    Identification of matches based on given "column_aa_position" of "df_label", which must be contained in "df_compare"
    "column_aa_position" must be an int, otherwise it is disregarded!

    Parameters
    __________
    df_label : product of get_aa_window_df --> labelled window slices
    df_compare : pd.DataFrame that contains the name_label (compare get_aa_window_labels) of df_label in a column
    column_id : the "ID" index of df_label must be identical to the column of df_compare, required for filtering!
    threshold : required matches in df_compare slices (sliced by column_id entries), standard is 2

    Returns
    _______
    df_label with modified labels
    """
    # identification list
    df_label_search_list = list(dict.fromkeys([str(index).split("__")[0] for index in df_label.index.tolist()]))
    # generate slices and iterate over df_label_search_list
    df_label_reset = df_label.reset_index()
    list_id = df_label_reset["ID"].to_numpy().tolist()
    df_compare_filtered = df_compare.dropna(subset=[column_id])
    position_seq_label = df_label.columns.tolist()[3]

    for query in df_label_search_list:
        # slice df_label
        # multilayer code for correct slice identification from df_label
        df_label_slice = df_label_reset[df_label_reset["ID"].str.contains(query)]
        arr_slice_positives = np.array([str(id_tag).split("__")[0] for id_tag in df_label_slice["ID"].tolist()])
        filter_list_slice_label = np.where(arr_slice_positives == query)
        df_label_slice = df_label_slice.iloc[filter_list_slice_label]

        list_available_pos = df_label_slice[position_seq_label].to_numpy().tolist()
        index_df_label_list = df_label_slice.index.tolist()

        # slice df_compare
        df_compare_slice_list_pos = (df_compare_filtered[df_compare_filtered[column_id].str.contains(query)]
                                     [position_seq_label].to_numpy().tolist())
        values, counts = np.unique(df_compare_slice_list_pos, return_counts=True)  # get pos in seq and their counts
        # the checking function
        for value, count in zip(values, counts):  # iterating over the pos in seq with their counts
            if count >= threshold:  # count of seq pos must be greater than the threshold
                if value in list_available_pos:  # is the seq pos in the label list?
                    id_df_label = list_id[index_df_label_list[list_available_pos.index(int(value))]]
                    df_label.loc[id_df_label, "label"] = 1
    modify_label_by_ident_column.describe = label_describe(df_label)[1]
    return df_label
