import pandas as pd
import numpy as np

def get_name_of_obj(obj, except_word = ""):
    '''Find object's name

    Parameters
    ----------------------
    except_word: str

    Returns
    ----------------------
    name: str
    '''
    
    for name, item in globals().items():
        if id(item) == id(obj) and name != except_word:
            return name

def check_lack(check_set,large_set,check_col_name,file_name = ""):
    '''Check the lack item which check set does not have 
       and large set has

    Parameters
    -----------------------------
    check_set, large_set: set of items
    check_col_name: str
        the name of the checked column
    file_name: str

    Returns
    ----------------------------
    set: the set of lack items
    '''
    
    if type(check_set) != set:
        check_set = set(check_set)
    
    for i in [None,-1]:
        if i in check_set:
            check_set.remove(i)

    if type(large_set) != set:
        large_set = set(large_set)
        
    lack_set = check_set - check_set.intersection(large_set)
    if len(lack_set) == 0:
        print("%s%s齐全，无需添加" %(file_name,check_col_name))
    else:
        for i in lack_set:
            print("%s%s不存在，请在%s里添加" %(check_col_name,i,file_name))
        print("%s有%d个%s缺失，请补充" %(file_name,len(lack_set),check_col_name))
        return lack_set
    
def easy_vlookup(to_df,from_df,left_keyword,right_keyword,vlookup_value,force=False,check=True):
    '''the same function with vlookup in excel'''
    
    is_lack = False
    if check:
        is_lack = check_lack(to_df[left_keyword],from_df[right_keyword],
                         left_keyword,get_name_of_obj(from_df))
    if is_lack == True and force == False:
        for i in is_lack:
            print(to_df[to_df.left_keyword == i])
        print('请添加缺失数据')
    else:
        to_df_index = to_df.index
        to_df = pd.merge(to_df,from_df[[right_keyword,vlookup_value]],
                        left_on = left_keyword,right_on=right_keyword,
                        how="left")
        to_df.index = to_df_index
        if right_keyword != left_keyword:
            del to_df[right_keyword]
        return to_df