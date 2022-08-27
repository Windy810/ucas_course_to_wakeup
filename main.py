from asyncore import write
import csv
import os
import re
import requests as r
from datetime import datetime
from bs4 import BeautifulSoup

from coursecalendar import Calendar
from httpRequestUtil_contextmanager import httpRequest


def error(msg):
    print(msg)
    os.system('pause')
    exit()

def genCSV(data_lists):
    header_list = ["课程名称","星期","开始节数","结束节数","老师","地点","周数"]
    with open("course.csv", mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header_list)
        writer.writerows(data_lists)

firstdayofterm = input("学期第一天的年月日，用'.'隔开，如2022.8.22：")
jsessionid = input('JSESSIONID：')

host = 'https://jwxk.ucas.ac.cn'
url = host + '/courseManage/main'

s = r.Session()
cookies = {
    'JSESSIONID': jsessionid # jwxk.ucas.ac.cn
}

firstday = datetime(*map(int, firstdayofterm.split('.')))
calendar = Calendar(firstday)

with httpRequest(s, url, 'get', cookies=cookies) as resp:
    # 解析"已选择课程"表格
    soup = BeautifulSoup(resp.content, 'html.parser')
    print('正在解析已选课程表格')
    table = soup.find('table')
    if not table:
        error('错误！无法解析已选课程表格，请检查jsessionid是否过期')
    choose = input("请选择需要的文件格式："+"\t"+"1. ics文件（导入日历）"+"\t"+"2. csv文件（导入课程表app）")
    data_lists = []
    for i, tr in enumerate(table.tbody.find_all('tr')):
        tds = tr.find_all('td')
        courseId = tds[0].a.getText()
        a_courseName = tds[1].a
        courseName = a_courseName.getText()
        courseTimeUrl = host + a_courseName['href']
        teacherName = tds[6].a.getText()
        print(f"{i+1:2}" + '. ' + courseId + '\t' + courseName)
        with httpRequest(s, courseTimeUrl, 'get') as resp2:
            # 解析上课时间
            soup2 = BeautifulSoup(resp2.content, 'html.parser')
            table2 = soup2.table
            if not table2:
                print('错误！无法获取课程时间表，暂时跳过。请确认选课系统中是否正确显示。')
                continue
            trs2 = table2.find_all('tr')
            groups = [(trs2[i].td.getText(), trs2[i+1].td.getText(), trs2[i+2].td.getText()) for i in range(0, len(trs2), 3)]
            
            if choose == "1":
                for time, place, week in groups:
                    calendar.appendCourse(courseId, courseName, time, place, week, teacherName)
            if choose == "2":
                numDict = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,'七': 7,"日":7}
                for time, place, week in groups:
                    # 星期三： 第1、2节。
                    numS = re.findall('(?<=期).*?(?=：)',time)
                    numS = ''.join(numS)
                    weekday = numDict[numS]
                    section = re.findall(r'\d+',time)
                    starttime = section[0]
                    endtime = section[len(section)-1]
                    data_list = [courseName,weekday,starttime,endtime,teacherName,place,week]
                    data_lists.append(data_list)
                genCSV(data_lists)
    
if choose == "1":
    print('解析完成，正在生成文件' + 'courses.ics')
    calendar.to_ics('courses.ics')
    print('成功！\n\n通过邮件等方式发送到手机后，即可导入到手机日历，安卓苹果通用。\n导入时建议新建一个日历账户，这样方便统一删除以及颜色区分。\n')
    os.system('pause')
if choose == '2':
    print('CSV课表制作完成，已成功生成文件' + 'course.csv')
    print('使用wakeup课程表的同学，建议将此文件发送至qq，用其它应用打开->导入到课程表')
    os.system('pause')


