from openpyxl import load_workbook
from collections import defaultdict
from urllib.parse import urlsplit
from kgtk import map_qnode

def openwb(workbook):
    wb = load_workbook(workbook)
    sheet = wb.active
    return sheet


def get_template_info(ep_files):
    kairos_ce = openwb(ep_files)
    template_info = defaultdict(list)
    for row in list(kairos_ce)[1:]:
        template_info[row[3].value] = row[4].value
    return template_info


def gold_label(EVAL_ep_file):
    wb = openwb(EVAL_ep_file)

    EVAL_ep = []
    EVAL_reference_ep = []
    for row in list(wb)[1:]:
        EVAL_ep.append(row[4].value.strip())
        EVAL_reference_ep.append(row[6].value.strip())
    return EVAL_ep, EVAL_reference_ep


def get_arg_list(arguments_file):
    # return argument list
    ce_arguments = openwb(arguments_file)
    ref_arguments_value = dict()
    ref_arguments_list = []
    for row in list(ce_arguments)[1:]:
        ref_arguments_value[row[3].value] = row[2].value
        ref_arguments_list.append(row[2].value.strip())
    return ref_arguments_value, ref_arguments_list


def qnode_mapping(ref_arguments_list):

    for v in ref_arguments_list:
        try:
            data_dict = map_qnode(v)
            qnode_ = [urlsplit(k['item']['value']).path.split('/')[-1] for k in data_dict]
            if qnode_ == []:
                length = len(v.split())
                # print(length)
                start = 1
                while start < length and qnode_ == []:
                    # print(' '.join(v.split()[start:]))
                    data_dict = map_qnode(' '.join(v.split()[start:]))
                    qnode_ = [urlsplit(k['item']['value']).path.split('/')[-1] for k in data_dict]
                    start += 1

            print([urlsplit(k['item']['value']).path.split('/')[-1] for k in data_dict])
        except:
            pass
            # print(k, v)
