# coding: utf-8

import os 
from collections import OrderedDict

import sqlite3
import requests
from win32.win32crypt import CryptUnprotectData
import pandas as pd

import xlwings as xw



# cookies(从浏览器中获取)
def getCookieFromChrome(host='yidian88.net'):
    cookiepath = r"C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Cookies"
    sql = "select host_key,name,encrypted_value from cookies where host_key='%s'" % host
    with sqlite3.connect(cookiepath) as conn:
        cu = conn.cursor()
        cookies = {
            name: CryptUnprotectData(encrypted_value)[1].decode()
            for host_key, name, encrypted_value in cu.execute(sql).fetchall()
        }
        print(cookies)
        return cookies


def output_excel(df,
                 path,
                 sheet_name="Sheet1",
                 range_position="A1",
                 mode='create',
                 index=True,
                 header=True):
    '''
        将dataframe输出至excel

        Parameters
        --------------------
        df: pd.DataFrame or dict
            dict: 值为pd.DataFrame的字典,快速导入多个DataFrame.
            pd.DataFrame: 导入单个DataFrame.

        path: str
            输出excel文件的地址

        sheet_name: str
            当导入单个DataFrame时有效,导入的表的名字.

        range_position: str
            当导入单个DataFrame时有效,导入的DataFrame处在表的位置.

        mode: {'create','replace'}
            create:新建excel文件
            replace:excel文件已存在,修改excel

        index: boolean
            是否导入索引

        header: boolean
            是否导入表头
        
    '''

    # 检查df的类型
    if type(df) != pd.core.frame.DataFrame and type(df) != dict and type(df) != OrderedDict:
        raise Exception(
            "invalid param 'df', type of 'df' must be DataFrame or dict")

    if type(df) == dict:
        for key in df:
            if type(df[key]) != pd.core.frame.DataFrame:
                raise Exception(
                    "invalid param 'df', type of 'df' is dict, type of df's values must be DataFrame"
                )

    # 检查path
    if type(path) != str:
        raise Exception("invalid param 'path'")

    # 检查sheet_name
    if not sheet_name:
        sheet_name = 'sheet1'
    if type(sheet_name) != str:
        raise Exception(
            "invalid param 'sheet_name',type of 'sheet_name' must be str or None."
        )

    # 检查sheet_name
    if not range_position:
        range_position = 'A1'
    if type(range_position) != str:
        raise Exception(
            "invalid param 'range_position',type of 'range_position' must be str or None."
        )

    # 检查mode
    if mode != 'create' and mode != 'replace':
        raise Exception(
            "invalid param 'mode', 'mode' must be 'create' or 'replace'")

    # 检查index
    if type(index) != bool:
        raise Exception(
            "invalid param 'index', type of 'index' must be boolean")

    # 检查header
    if type(header) != bool:
        raise Exception(
            "invalid param 'header', type of 'header' must be boolean")

    # 如果mode为新增
    if mode == 'create':

        if type(df) == pd.core.frame.DataFrame:
            writer = pd.ExcelWriter(path)
            df.to_excel(
                writer, sheet_name, index=index, header=header, encoding='utf-8')
            print("成功将df导入至文件%s的表%s中" %(os.path.basename(path),sheet_name))
            writer.save()
        elif type(df) == dict or type(df) == OrderedDict:
            writer = pd.ExcelWriter(path)
            for key in df:
                df[key].to_excel(
                    writer, key, index=index, header=header, encoding='utf-8')
                print("成功将DataFrame%s导入至文件%s的表%s中" %(key,os.path.basename(path),sheet_name))
            writer.save()
        else:
            print("导入失败，请检查df")

    elif mode == 'replace':

        if type(df) == pd.core.frame.DataFrame:

            app=xw.App(visible=False,add_book=False)
            app.display_alerts=False
            app.screen_updating=False

            # 打开工作簿
            wb=app.books.open(path)

            sheet_names = [sheet.name for sheet in wb.sheets]
            
            if sheet_name not in sheet_names:
                wb.sheets.add(sheet_name)
            wb.sheets[sheet_name].range(range_position).options(index=index, header=header).value = df
            print("成功将df导入至文件%s的表%s中" %(os.path.basename(path),sheet_name))

            wb.save()
            wb.close()
            app.quit()

        elif type(df) == dict or type(df) == OrderedDict:

            app=xw.App(visible=False,add_book=False)
            app.display_alerts=False
            app.screen_updating=False

            # 打开工作簿
            wb=app.books.open(path)
            sheet_names = [sheet.name for sheet in wb.sheets]

            for key in df:
                if key not in sheet_names:
                    wb.sheets.add(key)
                wb.sheets[key].range(range_position).options(index=index, header=header).value = df[key]
                print("成功将DataFrame%s导入至文件%s的表%s中" %(key,os.path.basename(path),sheet_name))

            wb.save()
            wb.close()
            app.quit()

    # 获取对象的名称
    def get_name_of_obj(obj, except_word = ""):
    
        for name, item in globals().items():
            if id(item) == id(obj) and name != except_word:
                return name

    # excel处理
    # 检查check_set是否包含于large_set
    def check_lack(check_set,large_set,check_col_name,file_name = "",):
        '''
        检查check_set是否包含于large_set

        parameters
        ---------------------
        check_set: set
        需匹配的列
        large_set: set
        被匹配的列
        check_col_name: str
        匹配列的列名
        file_name: str
        文件名
            
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
        
    def excel_vlookup(to_df,from_df,left_keyword,right_keyword,vlookup_value,force=False,check=True):
        '''
        excel中的vlookup

        Parameters
        ----------------------
        to_df: pd.DataFrame
        需匹配的表

        from_df: pd.DataFrame
        被匹配的表

        left_keyword: str
        需匹配的关键词的列名

        right_keyword: str
        被匹配的关键词的列名

        vlookup_value: str
        被匹配的内容的列名

        check: bool
        检查被匹配的列是否包含匹配的列

        force: bool
        在有缺失的情况系是否强制匹配

        '''
        
        is_lack = False
        if check:
            is_lack = check_lack(to_df[left_keyword],from_df[right_keyword],
                            left_keyword,get_name_of_obj(from_df))
        if is_lack == True and force == False:
            for i in is_lack:
                print(to_df[to_df.left_keyword == i])
            print('请添加缺失数据')
        else:
            to_df = pd.merge(to_df,from_df[[right_keyword,vlookup_value]],
                            left_on = left_keyword,right_on=right_keyword,
                            how="left")
            if right_keyword != left_keyword:
                del to_df[right_keyword]
            return to_df
            
