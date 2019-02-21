import os
import sqlite3 as lite
import sys
import time
from datetime import datetime

import pandas as pd
from pandas.io import sql

import contextlib


@contextlib.contextmanager
def connect_database(database_path):

    try:
        con = lite.connect(database_path)
        print("*"*40)
        print("成功连接数据库, 数据库地址为%s" %database_path)
        yield con
    except Exception as e:
        print("连接数据库失败, 数据库地址为%s" %database_path)
        print("原因如下:")
        print(e)
        print("*"*40)
    finally:
        print("关闭数据库连接, 数据库地址为%s" %database_path)
        print("*"*40)
        
@contextlib.contextmanager
def create_cursor(connect):

    try:
        cursor = connect.cursor()
        print("成功创建游标")
        yield cursor
    except Exception as e:
        print("创建游标失败")
        print("原因如下:")
        print(e)
        raise Exception("数据库载入异常")
    finally:
        print("关闭游标")
    



def save_dataframe(dataframe,
                   data_name,
                   data_unique_column_name,
                   create_data_table_sql,
                   mode=False,
                   database_path=""):
    '''保存下载数据至本地数据库'''

    # print(dataframe)
    # if len(dataframe) == 0:
    #     print('dataframe行数为0，不保存数据')
    #     return

    # 传入的数据的唯一列的集合
    if data_unique_column_name:
        dataframe_unique_set = set(dataframe[data_unique_column_name])

    time_now = False
    # 保存文件
    with connect_database(database_path) as con:

        with create_cursor(con) as cursor:
    
            time_before_load = time.time()
            try:

                if data_unique_column_name:
                    # 获取已存在的唯一列
                    alr_exist_list = list(
                        pd.read_sql(
                            "SELECT %s FROM %s" % (data_unique_column_name, data_name),
                            con=con,
                            index_col=data_unique_column_name).index)

                    # 如果是更新，则删除数据库中已存在的需要更新的数据
                    if mode == "update":

                        delect_list = list(
                            set(alr_exist_list).intersection(dataframe_unique_set))

                        # cursor.execute('Delete FROM %s WHERE %s IN %s' %
                        #                (data_name, data_unique_column_name,
                        #                 ",".join([str(x) for x in delect_set])))

                        for i in delect_list:
                            if data_name == "instock_collection_data":
                                cursor.execute('Delete FROM %s WHERE %s = "%s"' %
                                            (data_name, data_unique_column_name,
                                                str(i)))
                            else:
                                cursor.execute('Delete FROM %s WHERE %s == %s' %
                                            (data_name, data_unique_column_name,
                                                str(i)))
                    elif mode == "replace":
                        cursor.execute('Delete FROM %s' % data_name)

                else:
                    pass

                # 执行完语句记得关闭
                cursor.close()

                print("成功载入%s数据库表,共耗时%.2f秒" % (data_name,
                                            (time.time() - time_before_load)))

            except pd.io.sql.DatabaseError as e:  # 如果出现操作错误

                # 检查错误信息
                if ("no such table: %s" % data_name) in str(e):
                    # 如果是表不存在
                    print("没有%s的表，请检查数据库文件" % data_name)

                    #创建数据库表
                    cursor = con.cursor()
                    cursor.execute(create_data_table_sql)
                    cursor.close()

                    alr_exist_list = []
                else:
                    print("保存%s数据时出现未知错误，请检查。错误信息：%s" % (data_name, str(e)))
                    print("保存%s数据失败，放弃保存" % data_name)

                    # 退出之前，关闭游标及数据库连接
                    cursor.close()
                    con.close()
                    return
            # 保存数据至数据库
            print("开始保存表%s" % data_name)

            #
            if data_unique_column_name:
                if mode== "update":
                    save_data = dataframe
                    print("系统已存在%d条数据，要更新%d条数据，新增%d数据，总计%d条数据" % (
                        len(alr_exist_list),  #已存在的数据的行数
                        len(set(alr_exist_list)
                            .intersection(dataframe_unique_set)),  #要更新的数据的行数
                        len(dataframe_unique_set) -
                        len(set(alr_exist_list)
                            .intersection(dataframe_unique_set)),  #新增的数据的行数
                        len(alr_exist_list) + len(dataframe_unique_set) -
                        len(set(alr_exist_list)
                            .intersection(dataframe_unique_set))))  #所有数据的行数
                elif mode == "replace":
                    save_data = dataframe
                    print("系统已存在%d条数据，删除原表, 重新保存%d条数据" %
                        (len(alr_exist_list), len(save_data)))
                else:
                    save_data = dataframe[
                        ~dataframe[data_unique_column_name].isin(alr_exist_list)]
                    print("系统已存在%d条数据，要保存%d条数据，总计%d条数据" %
                        (len(alr_exist_list), len(save_data),
                        len(alr_exist_list) + len(save_data)))
            else:
                save_data = dataframe
                print("保存%d条数据" % len(save_data))
                
            sql.to_sql(
                save_data,
                name=data_name,
                con=con,
                index=False,  # 是否将index作为column导入数据库
                #How to behave if the table already exists.
                # fail: Raise a ValueError.
                # replace: Drop the table before inserting new values.
                # append: Insert new values to the existing table.
                if_exists='append')
            print("成功保存表%s" % data_name)
            print("*" * 40)
            # 返回最后更新时间
            time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        con.commit()
        return time_now if time_now else None
        
def save_last_update_time(database_path, data_name, update_time):
    '''
    Parameters
    ---------------------
    database_path: str
        数据库地址
    data_name: str
        数据名称
    update_time: datetime
        更新日期
    '''

    with connect_database(database_path) as con:

        is_table_exist = False

        # 获取已存在的唯一列
        try:

            with create_cursor(con) as cursor:
                cursor.execute('''select data_name from update_detail''')
                records = cursor.fetchall()

            alr_exist_data_name_list = [record[0] for record in records]

            is_table_exist = True
            # print(alr_exist_data_name_list)
        except:
            create_table = '''CREATE TABLE update_detail (
                data_name_id     INTEGER UNIQUE
                                        PRIMARY KEY,
                data_name        TEXT    UNIQUE,
                last_update_time TEXT
            );'''

            # 创建表
            with create_cursor(con) as cursor:
                cursor.execute(create_table)


        execute_sql = ""
        if is_table_exist and data_name in alr_exist_data_name_list:  # 如果表存在且查看所要更新的data_name是否存在

            execute_sql = "UPDATE update_detail SET last_update_time = '%s' where data_name = '%s'" % (
                update_time, data_name)
        else:
            # 不存在则insert时间记录
            execute_sql = "INSERT INTO update_detail (data_name,last_update_time) VALUES ('%s','%s');" % (
                data_name, update_time)

        with create_cursor(con) as cursor:
            cursor.execute(execute_sql)

        print('更新完毕,最后更新时间')

        con.commit()
