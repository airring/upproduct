#encoding:utf-8
import sys
import os
import socket
import time
import flask3

local_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
base_arg = ('pf', 'db','pom')
all_arg = ('notice', 'user', 'userprofile', 'query', 'assets', 'bankservice', 'borrow',
           'operate', 'pay', 'plan', 'trade', 'task', 'APIGateway', 'signature')
jar_arg = ('smallloans', 'label', 'autoop')


#############修改配置文件
def change_config(arg):
    if os.path.exists("/home/%s/js/util/common.js" % arg) == True:
        os.system(
            'sed -i "s/http:\/\/localhost\/rrjcoperatemanage/http:\/\/183.57.43.79:12080\/rrjcoperatemanage/" /home/%s/js/util/common.js' % arg)
    elif arg == 'rrjc-signature':
        os.system('\cp -f /root/conf/%s/jdbc.properties   /home/%s/WEB-INF/classes/jdbc.properties' % (arg, arg))
        os.system(
            '\cp -f /root/conf/%s/dubbo.properties   /home/%s/WEB-INF/classes/config/dubbo.properties' % (arg, arg))
        os.system('\cp -f /root/conf/%s/init.properties   /home/%s/WEB-INF/classes/config/init.properties' % (arg, arg))
        os.system(
            '\cp -f /root/conf/%s/redis.properties   /home/%s/WEB-INF/classes/config/redis.properties' % (arg, arg))
    else:
        os.system('\cp -f /root/conf/%s/jdbc.properties   /home/%s/WEB-INF/classes/jdbc.properties' % (arg, arg))
        os.system(
            '\cp -f /root/conf/%s/dubbo.properties   /home/%s/WEB-INF/classes/dubbo/dubbo.properties' % (arg, arg))
        os.system('\cp -f /root/conf/%s/init.properties   /home/%s/WEB-INF/classes/init.properties' % (arg, arg))
        os.system(
            '\cp -f /root/conf/%s/redis.properties   /home/%s/WEB-INF/classes/redis/redis.properties' % (arg, arg))
        os.system(
            '\cp -f /root/conf/%s/mongo.properties   /home/%s/WEB-INF/classes/mongo/mongo.properties' % (arg, arg))


def unzip_pro(arg):
    war_file = os.popen('find /home/tomcat8/rrjcsvn/rrjc-%s -name rrjc-*.war' % arg)
    for i in war_file:
        if 'impl' in i:
            pro_name = i.split('/')[-1].split('.')[0].split('-')[1]
            pro_name = 'rrjc-' + pro_name
        else:
            pro_name = i.split('/')[-1].split('.')[0]
        os.system('rm /home/%s/* -rf 2>1 >/dev/null' % pro_name)
        os.system('unzip -o -q -d /home/%s %s ' % (pro_name, i))
        if os.path.exists('/home/rrjctomcat/%s' % local_time) == False:
            os.mkdir('/home/rrjctomcat/%s' % local_time)
        i = i.split()[0]
        os.system("mv %s /home/rrjctomcat/%s/%s.war" % (i, local_time, pro_name))
        change_config(pro_name)


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
    os.chdir('/home/tomcat8/rrjcsvn/rrjc-%s' % arg)
    os.system('git fetch --all  2>1 >/dev/null')
    os.system('git reset --hard origin/master 2>1 >/dev/null')
    os.system('git pull origin master 2>1 >/dev/null')
    os.system(
        '\cp -f /root/conf/rrjc-%s/application.properties /home/tomcat8/rrjcsvn/rrjc-%s/rrjc-%s-impl/src/main/resources/application.properties' % (
        arg, arg, arg))
    if os.system('mvn clean install deploy -e -Dmaven.test.skip=true 2>1 > /tmp/build-%s' % arg) == 0:
        print('%s 编译成功' % arg)
    else:
        print('%s 编译失败' % arg)
        exit()
    file_name = os.popen('find ./ -name rrjc-%s-impl-*.jar' % arg).read()
    os.system('mkdir  /home/rrjc-%s' % arg)
    os.system('rm -f   /home/rrjc-%s/*.jar' % arg)
    os.system('\cp -f  /home/tomcat8/rrjcsvn/rrjc-%s/rrjc-%s-impl/target/rrjc-*.jar   /home/rrjc-%s/rrjc-%s.jar' % (
    arg, arg, arg, arg))
    if os.path.exists('/home/rrjctomcat/%s' % local_time) == False:
        os.mkdir('/home/rrjctomcat/%s' % local_time)
    os.system('mv  /home/tomcat8/rrjcsvn/rrjc-%s/rrjc-%s-impl/target/rrjc-%s.jar   /home/rrjctomcat/%s/rrjc-%s.jar' % (
    arg, arg, arg, local_time, arg))
    os.chdir('/home/rrjc-%s' % arg)
    # os.system('nohup java -server -Xms512m -Xmx512m -XX:PermSize=128m -XX:MaxPermSize=256m -XX:MaxNewSize=128m -jar rrjc-%s.jar 2>&1 & > /tmp/%s.log' % (arg,arg))
    sys.exit(0)


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
