# -*- coding:utf-8 -*-
import sys, os, re, sqlite3, time, MeCab
from operator import itemgetter
from email.utils import parsedate
from datetime import datetime as dt

""" グローバル変数 """
fileDbName = "filedb.sqlite3"
path = "./staff_wr_origin/201707.month/"
name = "dummy" # 名前記録用

def translateFunc(fileName, key):
    global path, name
    try:
        constructor = open(path+"%s" % (fileName), 'r')
        pattern = re.compile(key, re.I)
        leaderFlag = 0
        try:
            for i in constructor.readlines():
                if key == "Date":
                    if pattern.match(i):
                        d = time.strftime('%Y/%m/%d %H:%M:%S', parsedate(i.replace('Date:', ''))) #時間文字列に変換
                elif key ==  "From":
                    if pattern.match(i):
                        d = (re.sub('\<.+\>', '', i.replace("From:", ''))).replace(' ','')
                        d = d.replace('\n', '')
                        d = d.replace('ドリーム・アーツ', '')
                        d = re.sub(re.compile('dreamarts',re.I), '', d)
                        name = d #名前記録．
                else:
                    if pattern.match(i):
                        d = i.replace("Subject:", '')
                        e = re.search('\[.+_WR\]', d).group()
                        if e != None:
                            f = ((e.replace('[', '')).replace('_WR', '')).replace(']', '')
                            if f == 'PM':
                                leaderFlag = 1 #リーダーかを判定．
                            d = (((d.replace(' ','')).replace('\n', '')).replace( e, '' )).replace(name, '')
                            j = list(d.split("_"))[2]
                            j = j.replace('PD', 'プロダクト開発')
                        else:
                            print "Error, by leaderFlag."
                            sys.exit()
            constructor.close() 
        except Exception, err: 
            constructor.close() 
            print 'got exception:%s\n' % (err)
            return
        finally:                              
            constructor.close() 
            if key == "Date" or key == "From":
                if d:
                    return d
                else:
                    return
            else:
                if j:
                    return (j, leaderFlag)
                else:
                    return
    except:
        print 'cannot open file: %s' % (fileName)
        # sys.exit()

def checkFileExist(fileName):
    global fileDbName, path
    access = sqlite3.connect("./"+fileDbName)
    c = access.cursor()
    sql = ('select * from file where file_name = "%s";' % fileName)
    c.execute(sql)
    result = c.fetchall()
    print(result)
    if len(result) != 0:
        access.close()
    else:
        #ファイルがdbに関連づけられていない場合．
        #正規表現で必要なカラム情報を抜き出す．
        #insertでdbへ追加処理.
        date = translateFunc(fileName, 'Date')
        if date != None:
            print "#####################"
            print date
            datetimeObj = dt.strptime(date, '%Y/%m/%d %H:%M:%S') #文字列>>datetimeObj
            yearNum = datetimeObj.year
            monthNum = datetimeObj.month
            dayNum = datetimeObj.day
            weekNums = dt(yearNum, monthNum, dayNum).isocalendar()
        else:
            print 'Error, translateDate()'
            sys.exit()

        authorName = translateFunc(fileName, 'From')
        if authorName != None:
            print"######################"
            print authorName
        else:
            print 'Error, translatesAuthor()'
            sys.exit()
        

        tmp = translateFunc(fileName, 'Subject')
        if tmp != None:
            groupName = tmp[0]
            leaderFlag = tmp[1]
            if groupName != None:
                print "###################"
                print groupName
                print leaderFlag
            else:
                print 'Error, translatesSubject()'
                sys.exit()
        else:
            return #Subjectで例外があったら除外する．

        sql2 = ('select id from department where name = "%s";' % groupName)
        c.execute(sql2)
        result2 = c2.fetchall()
        if len(result2) != 0:
            if len(result2) == 1:
                departmentId = (result2[0])[0]
            else:
                print "Warning : departmentDbに同じ部署が複数ある．"
                access.close()
                sys.exit()
        else:
            sql2 = ('insert into department(name) values("%s");' % groupName)
            c.execute(sql2)
            access.commit()
            sql2 = ('select id from department where name = "%s";' % groupName)
            c.execute(sql2)
            result2 = c.fetchall()
            if len(result2) != 0:
                if len(result2) == 1:
                    departmentId = (result2[0])[0]
                else:
                    print "Warning : departmentDbに同じ部署が複数ある．(After insert)"
                    access.close()
                    sys.exit()
        
        sql3 = ('select id from employee where name = "%s";' % authorName)
        c.execute(sql3)
        result3 = c.fetchall()
        if len(result3) != 0:
            if len(result3) == 1:
                employeeId = (result3[0])[0]
            else:
                print "Warning : employeeDbに同じ名前が複数ある．"
                access.close()
                sys.exit()
        else:
            sql3 = ('insert into employee(name) values("%s");' % authorName)
            c.execute(sql3)
            access.commit()
            sql3 = ('select id from employee where name = "%s";' % authorName)
            c.execute(sql3)
            result3 = c.fetchall()
            if len(result3) != 0:
                if len(result3) == 1:
                    employeeId = (result3[0])[0]
                else:
                    print "Warning : employeeDbに同じ名前が複数ある．(After insert)"
                    access.close()
                    sys.exit()
        #sql = ('insert into file(employee_id, date, department_id, is_leader, file_name) values(%d, %s, %d, %d, %s);' % (employeeId, date, departmentId, leaderFlag, fileName))
        sql = ('insert into file(employee_id, weekNum, yearNum, department_id, is_leader, file_name) values(?, ?, ?, ?, ?, ?);')
        c.execute(sql, [employeeId, weekNums[1], weekNums[0], departmentId, leaderFlag, fileName])
        access.commit()
        access.close()



def filtering(post, dateData):
    global fileDbName
    access = sqlite3.connect(fileDbName)
    fileNameList = access.cursor()
    c = access.cursor()
    sql2 = ('select id from department where name = "%s"' % post)
    if dateData != None:
        datetimeObj = dt.strptime(dateData, '%Y/%m/%d')
        weekNums = dt(datetimeObj.year, datetimeObj.month, datetimeObj.day).isocalendar()
    try:
        c.execute(sql2)
    except sqlite3.Error as e:
        print "データベースにその所属部署は存在しない．"
        access.close()
        return []
    finally:
        result2 = c2.fetchall()
        if len(result2) == 0:
            print "データベースにその所属部署は存在しない．"
            access.close()
            return []
    if dateData != None:
        try:
            sql = ("select file_name from file where is_leader = 0 and department_id = %d and weekNum = %d and yearNum = %d;" % ((result2[0])[0], weekNums[1], weekNums[0])) #リーダーでなくて，かつ週数，年月が同じの場合のファイル名を探索．
            fileNameList.execute(sql)
        except sqlite3.Error as e:
            print "データベースにその週の所属部署の記録がない．"
            access.close()
            return []
    else:
        try:
            sql = ("select yearNum from file where is_leader = 0 and department_id = %d;" % (result2[0])[0])
            fileNameList.execute(sql)
            tmp = fileNameList.fetchall()
            tmp.sort(key=lambda x: x[0], reverse=True)
            maxYearNum = (tmp.pop(0))[0]
            sql = ("select weekNum from file where is_leader = 0 and department_id = %d and yearNum = %d;" % ((result2[0])[0], maxYearNum))
            fileNameList.execute(sql)
            tmp = fileNameList.fetchall()
            tmp.sort(key=lambda x: x[0], reverse=True)
            maxWeekNum = (tmp.pop(0))[0]
            sql = ("select file_name from file where is_leader = 0 and department_id = %d and yearNum = %d and weekNum = %d;" % ((result2[0])[0], maxYearNum, maxWeekNum))
            fileNameList.execute(sql)
            #tmp = fileNameList.fetchall()
            #print tmp
        except sqlite3.Error as e:
            print "部下のデータがないなどのエラー．:"+str(e)
            access.close()
            return []

    answerList = fileNameList.fetchall()
    access.close()
    return answerList


def sendMecab(dName, dDate):
    """
    指定の部署メンバーのWRをMeCabで形態素解析し、結果を返す。

    Args:
        dName (str): 部署名
        dDate (?): 年月日

    Returns:
        unionOfWR (str): 形態素解析の結果
    """
    fileList = filtering(dName, dDate)
    if len(fileList) == 0:
        return "その部署はないか、その部署の指定期間のWEEKLY REPORTはありません。"

    unionOfWR = ""
    for tmp in fileList:
        f = open(path+tmp[0], 'r')
        m = MeCab.Tagger ("-Owakati")
        sentences = f.read()
        sentences = re.sub(r'[-=]+','', sentences)
        test = re.split('\n\n<< WEEKLY REPORT >>', sentences)
        sentences = sentences.replace(test[0], '')
        unionOfWR += (m.parse(sentences))

    return unionOfWR


def main():
    """
    main
    """
    global path
    files = os.listdir(path)
    filesPathFactorList = []
    for x in files:
        if os.path.isfile(path + x):
            if (re.search('\.mes\.utf', x) is not None):
                filesPathFactorList.append(x)

    for fileName in filesPathFactorList:
        if(fileName[-4:] == '.utf'): 
            checkFileExist(fileName) # データベースにファイルが関連付けられているか．いない場合，追加処理を行う．

    post = list(raw_input().split())
    
    if len(post) == 1:
        fileList = filtering(post[0], None)
    elif len(post) == 2:
        fileList = filtering(post[0], post[1])
    else:
        pass


if __name__ == '__main__':
        main()
