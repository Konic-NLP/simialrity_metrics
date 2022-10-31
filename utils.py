from openpyxl import load_workbook
from collections import defaultdict
from urllib.parse import urlsplit
from kgtk import map_qnode

def openwb(workbook):
    '''
    return the workbook of the excel
    :param workbook: excel file
    :return: the sheet of that excel file
    '''
    wb = load_workbook(workbook)
    sheet = wb.active
    return sheet


def get_template_info(ep_files):
    '''
    use for extract the fillers from the slots in the template and compute the lexical overlapping score
    :param ep_files:  system event excel files
    :return:   a dict , key is the id of the events, and the value is the template of that event
    '''
    kairos_ce = openwb(ep_files)
    template_info = defaultdict(list)
    for row in list(kairos_ce)[1:]:
        template_info[row[3].value] = row[4].value
    return template_info


def gold_label(EVAL_ep_file):
    '''
    get the ground truth for the event match


    :param EVAL_ep_file:  human assessment excel file for event match
    :return:  two list, one records  the system id, and the other records the corresponding reference id if matched, other wse
    records 'n/a'
    '''
    wb = openwb(EVAL_ep_file)

    EVAL_ep = []
    EVAL_reference_ep = []
    for row in list(wb)[1:]:
        EVAL_ep.append(row[4].value.strip())
        EVAL_reference_ep.append(row[6].value.strip())
    return EVAL_ep, EVAL_reference_ep


def get_arg_list(arguments_file):
    '''
    one dict storethe id , argument pair, the other is a list

    :param arguments_file:
    :return:
    '''
    # return argument list
    ce_arguments = openwb(arguments_file)
    ref_arguments_value = dict()
    ref_arguments_list = []
    for row in list(ce_arguments)[1:]:
        ref_arguments_value[row[3].value] = row[2].value
        ref_arguments_list.append(row[2].value.strip())
    return ref_arguments_value, ref_arguments_list


def qnode_mapping(ref_arguments_list):
    '''

    map the qnode use the map_qnode function including the SPARAL
    initial n=all tolens of the argument value
    then n-=1
    return a list that matches the argument value or [] until n=1
    :param ref_arguments_list:
    :return:  qnode list that matches the argument value based on SPARAL
    '''
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
