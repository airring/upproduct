#encoding:utf-8
import sys
import os
import socket
import time
import flask3

local_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
base_arg = ('a', 'b','c')
all_arg = ('ba', 'user', 'users', 'dsa')
jar_arg = ('kar', 'bsdsa', 'fsad')


#############修改配置文件
def change_config(arg):
	pass

def unzip_pro(arg):
	pass


# 编译APIgateway

def build_api():
    time.sleep(1)
    global build_static
    build_static = 1
    global update_file
    update_file=u'api.txt'

####### 编译服务
def build_pro(arg):
    time.sleep(1)
    global build_static
    build_static=1
    global update_file
    update_file = u'1.txt,2.txt'

def build_jar(arg):
	pass


# 重启服务
list_tomcat = []


def uniq_tomcat(arg):
    if os.popen("find /usr/local/tomcat* -name server.xml |xargs  grep -rl rrjc-%s | wc -l" % arg).read().split('\n')[
        0] != '0':
        pro_tomcat = os.popen(
            "find /usr/local/tomcat* -name server.xml |xargs  grep -rl rrjc-%s | awk -F / '{print $4}'" % arg).read().split()[
            0]
        list_tomcat.append('%s' % pro_tomcat)
    elif arg == 'APIGateway':
        pro_tomcat = os.popen(
            "find /usr/local/tomcat* -name server.xml |xargs  grep -rl %s | awk -F / '{print $4}'" % arg).read().split()[
            0]
        list_tomcat.append('%s' % pro_tomcat)

    else:
        print("%s 不存在" % arg)


def restart_pro(arg):
    if os.popen("ps aux | egrep -v 'grep|cron' | grep -v sh|grep %s |grep java |  wc -l" % arg).read().split('\n')[
        0] != '0':
        tomcat_pid = os.popen(
            "ps aux | egrep -v 'grep|cron' | grep -v sh| grep java |grep %s | awk '{print $2}'" % arg).read().split()[0]
        os.system('kill -9 %s' % tomcat_pid)
    os.system('rm /usr/local/%s/work/Catalina -rf' % arg)
    os.system('/usr/local/%s/bin/startup.sh' % arg)


def restart_now(arg):
    for i in arg:
        uniq_tomcat(i)
    list_tomcat1 = set(list_tomcat)
    for y in list_tomcat1:
        restart_pro(y)
