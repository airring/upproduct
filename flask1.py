#encoding: utf-8
from flask import Flask,redirect,url_for,render_template,request,session
from flask_sqlalchemy import SQLAlchemy
#from celery import Celery
import os,socket,time
import config,ArgInput
from gevent import monkey
from gevent import pywsgi

####字符集
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

monkey.patch_all()

app = Flask(__name__)
############加载db配置
app.config.from_object(config)
##############session加盐
app.config['SECRET_KEY'] = '~\xc8\xc6\xe0\xf3,\x98O\xa8z4\xfb=\rNd'
db=SQLAlchemy(app)
###########异步处理redis

#########定义时间

class t_user(db.Model):
	id = db.Column(db.Integer,primary_key=True,autoincrement=True)
	username = db.Column(db.String(20),nullable=False,index=True,unique=True)
	password = db.Column(db.String(20),nullable=False)
	group_id = db.Column(db.Integer,db.ForeignKey('t_group.id'))

class t_group(db.Model):
	id = db.Column(db.Integer,primary_key=True,autoincrement=True)
	group_name = db.Column(db.String(20),index=True)
	####### 1 admin  2管理员
	quanxian = db.Column(db.Integer)
	devlimit = db.Column(db.Integer)
	testlimit = db.Column(db.Integer)
	releaselimit = db.Column(db.Integer)
	chanplimit = db.Column(db.Integer)


class t_update(db.Model):
	user_id = db.Column(db.Integer, db.ForeignKey('t_user.id'))
	pro_name = db.Column(db.String(20),nullable=True)
	update_time = db.Column(db.DateTime,primary_key=True)
	uppro_time = db.Column(db.DateTime,primary_key=True)
	#######状态=1 开发提交 2 测试审计 3 测试通过 4 发布上线
	static = db.Column(db.Integer)

class t_log(db.Model):
	id = db.Column(db.Integer,primary_key=True,autoincrement=True)
	user_id = db.Column(db.Integer, db.ForeignKey('t_user.id'))
	sj_username = db.Column(db.String(20))
	up_username = db.Column(db.String(20))
	pro_name = db.Column(db.String(20),nullable=True)
	note = db.Column(db.Text,nullable=True)
	branch = db.Column(db.Text)
	update_time = db.Column(db.Integer)
	uppro_time = db.Column(db.Integer)
	#预发布上线次数
	uptimes = db.Column(db.Integer)

	static = db.Column(db.Integer)

db.create_all()


def build_static():
	for i in request.form.getlist('service_choies'):
		static = t_log.query.filter(t_log.id == i).first()
		if static.pro_name == 'pf':
			os.system('find /home/tomcat8/rrjcsvn -name *.war |xargs rm -f')
			ArgInput.build_pro(static.pro_name)
		elif static.pro_name == 'APIGateway':
			ArgInput.build_api()
		elif static.pro_name in ArgInput.jar_arg:
			ArgInput.build_jar(static.pro_name)
		else:
			ArgInput.build_pro(static.pro_name)
		ArgInput.uniq_tomcat(static.pro_name)
		static.update_file=ArgInput.update_file
		if ArgInput.build_static:
			static.build_static=(u'%s 编译成功' % static.pro_name)
		else:
			static.build_static=(u'%s 编译失败' % static.pro_name)
			static.error_log=ArgInput.error_log
		#########重启预发布
	list_tomcat1 = set(ArgInput.list_tomcat)
	for y in list_tomcat1:
		ArgInput.restart_pro(y)

		static.static = 3
		db.session.commit()



###########状态对应
status_ck = {}
class_status = {}
status_ck[1]=u"测试审批中"
status_ck[2] = u"预发布编译中"
status_ck[3] = u"预发布已编译"
status_ck[4] = u"生产上线中"
status_ck[5] = u"产品验收通过"
status_ck[15] = u"生产已上线"
status_ck[14] = u"预发布编译失败"
status_ck[13] = u"生产同步失败"
class_status[1] = u'label-warning'
class_status[2] = u'label-warning'
class_status[3] = u'label-info'
class_status[4] = u'label-warning'
class_status[15] = u'label-success'
class_status[14] = u'label-danger'
class_status[13] = u'label-danger'






@app.route('/')
def hello_world():

	return redirect('/login.html')


#############判断登陆###########
@app.route('/login.html', methods=['GET','POST'])
def login():
	if 'username' in session:
		return render_template('service.html' ,username=session['username'])
	if request.method == 'POST':
		login_username = request.values.get('username')
		login_password = request.values.get('password')
		db_password = t_user.query.filter(t_user.username == login_username).first()
		if db_password:
			if db_password.password == login_password:
				session['group_id'] = db_password.group_id
				session['username'] = login_username
				session['user_id'] = db_password.id


				return redirect('pro_static.html')
			else:
				return '密码错误'
		else:
			return '用户不存在'
	else:

		return render_template('login.html')

@app.route('/logout.html')
def logout():
	session.pop('username')
	return redirect('/login.html')

@app.route('/index.html')
def index():
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().devlimit != 1:
			return render_template('error.html')
		return render_template('index.html',services=ArgInput.all_arg,baseserver=ArgInput.base_arg,
							   jarserver=ArgInput.jar_arg,branchserver=ArgInput.branch_arg,upproservice=ArgInput.uppro_arg)
	else:
		return redirect('/login.html')

@app.route('/pro_static.html',methods=['POST','GET'])
def pro_static():
	if 'username' in session:
		if request.method == 'POST':
			serverices_name = request.form.getlist('service_choice')
			up_note = request.form.get('note')
			# for i in serverices_name:
			#
			# 	date_time=

			# 	add_t_log = t_log(user_id=session['user_id'], pro_name=i, note=up_note, update_time=int(time.time()),uptimes=1, static=1)
			# 	db.session.add(add_t_log)
			# 	db.session.commit()

		db_logs = t_log.query.order_by(t_log.update_time.desc()).all()

		##########状态判断
		for i in db_logs:

			i.status = status_ck[i.static]
			i.class_status=class_status[i.static]

			i.username=t_user.query.filter(t_user.id ==i.user_id).first().username

			i.uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.update_time))

			if i.uppro_time:
				i.uppro = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.uppro_time))
			else:
				i.uppro = u'未上线'

		return render_template('pro_static.html' ,db_logs=db_logs)

	else:
		return redirect('/login.html')

###########预发布审计
@app.route('/shenji.html',methods=['POST','GET'])
def shenji():
	if 'username' in session:
		##########审计鉴权
		if t_group.query.filter(t_group.id == session['group_id']).first().testlimit != 1:
			return render_template('error.html')
		build_server=[]
		ArgInput.list_tomcat=[]
		for i in request.form.getlist('service_choies'):
			######更新状态
			static = t_log.query.filter(t_log.id == i).first()
			if static.static != 1:
				static.uptimes = static.uptimes + 1
			static.static = 2
			static.update_time = int(time.time())
			db.session.commit()
		#########编译项目
		for i in request.form.getlist('service_choies'):
			static = t_log.query.filter(t_log.id == i).first()
			if static.pro_name == 'pf':
				os.system('find /home/tomcat8/rrjcsvn -name *.war |xargs rm -f')
				ArgInput.build_pro(static.pro_name)
			elif static.pro_name == 'APIGateway':
				ArgInput.build_api()
			elif static.pro_name in ArgInput.jar_arg:
				ArgInput.build_jar(static.pro_name)
			elif static.pro_name == 'rrjc':
				os.system(
					'ansible 192.168.1.102 -m shell -a "source /etc/profile; ~/bianyi.sh %s" >/tmp/build-rrjc' % static.branch)
				ArgInput.update_file=os.popen("sed -n '/start to check svn code/,/end to check svn code/p' /tmp/build-rrjc").read()
				ArgInput.build_static = int(os.popen("cat /tmp/build-rrjc |egrep 'BUILD SUCCESSFUL' |wc -l").read().split('\n')[0])
				print ArgInput.build_static
				ArgInput.error_log = os.popen("cat /tmp/build-rrjc").read()
				os.system('ansible 192.168.1.102 -m shell -a "source /etc/profile;nohup /usr/local/tomcat678/bin/startup.sh &"')
			elif static.pro_name in ArgInput.branch_arg:
				ArgInput.build_branch(static.pro_name,static.branch)
				ArgInput.update_file=u'该项目暂不支持显示'
				ArgInput.build_static = 1
			elif static.pro_name in ArgInput.uppro_arg:
				ArgInput.build_static = 1
				ArgInput.update_file=u'该项目无预发布环境'
			else:
				ArgInput.build_pro(static.pro_name)
			ArgInput.uniq_tomcat(static.pro_name)
			i = {}
			i['update_file']=ArgInput.update_file
			if ArgInput.build_static == 1:
				i['build_static']=(u'%s 编译成功' % static.pro_name)
				static.static = 3
				static.update_time=int(time.time())
				static.sj_username=session['username']
				db.session.commit()
			else:
				i['build_static']=(u'%s 编译失败' % static.pro_name)
				i['error_log']=ArgInput.error_log
				static.static = 14
				static.update_time = int(time.time())
				db.session.commit()

			build_server.append(i)
		#########重启预发布
		list_tomcat1 = set(ArgInput.list_tomcat)
		for y in list_tomcat1:
			ArgInput.restart_pro(y)


		return render_template('shenji.html' ,static=build_server)

#########生产审计
@app.route('/proshenji.html',methods=['POST','GET'])
def proshenji():
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().testlimit != 1:
			return render_template('error.html')
		build_server = []
		for i in request.form.getlist('service_choies'):
			######更新状态

			static = t_log.query.filter(t_log.id == i).first()
			static.static = 4
			static.update_time = int(time.time())
			db.session.commit()
		#########同步生产
		for i in request.form.getlist('service_choies'):
			static = t_log.query.filter(t_log.id == i).first()
			i = {}
			if static.pro_name == 'rrjc':
				os.system('/home/fabu/script/tongburrjc.sh')
				static.uppro_time = int(time.time())
				static.static = 15
			elif static.pro_name in ArgInput.base_arg:
				static.uppro_time = int(time.time())
				static.static = 15
			elif static.pro_name in ArgInput.branch_arg:
				os.system('/home/fabu/script/tongbuwap.sh')
				static.uppro_time = int(time.time())
				static.static = 15
			########预发布无环境直接上线项目
			elif static.pro_name in ArgInput.uppro_arg:
				os.system('/home/fabu/script/sv%s.sh > /tmp/build-%s' % static.pro_name,static.pro_name)
				static.static = 15
				static.uppro_time = int(time.time())
			else:
				src_path=os.popen('find /home/rrjctomcat/%s |grep %s\. ' % (ArgInput.local_time,static.pro_name)).read().split('\n')[0]
				if src_path == '':
					i['build_static'] = u'%s 发布失败' % static.pro_name
					static.static = 13
				else:
					os.system('ansible-playbook /home/ansible/service/%s.yml -e  "service_name=%s  src_file=%s  local_time=%s" > /tmp/build-%s'% (static.pro_name,static.pro_name,src_path,ArgInput.local_time,static.pro_name) )
					i['build_static'] = u'%s 发布成功' % static.pro_name
					i['update_file'] = os.popen("sed -n '/PLAY RECAP/,//p' /tmp/build-%s" % static.pro_name).read()
					static.uppro_time = int(time.time())
					static.static = 15
			static.up_username = session['username']
			db.session.commit()
			build_server.append(i)
		return render_template('shenji.html' , static=build_server)

@app.route('/devshenji.html',methods=['POST','GET'])
def devshenji():
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().devlimit != 1:
			return render_template('error.html')

		build_server=[]
		serverices_name = request.form.getlist('service_choice')
		up_note = request.form.get('note')
		for i in serverices_name:
			a={}
			exist_pro_name = t_log.query.filter(t_log.static != 15,t_log.pro_name == i).all()
			if exist_pro_name:
				a['build_static'] = u'%s 已经存在发布状态中' % i
				continue

			a['build_static'] = u'%s 已经提交审批' % i
			date_time=time.localtime(time.time())
			add_t_log = t_log(user_id=session['user_id'], pro_name=i, note=up_note, update_time=int(time.time()),uptimes=1, static=1,branch=request.form.get(i))
			db.session.add(add_t_log)
			db.session.commit()
	return render_template('shenji.html', static=build_server)

@app.route('/checkshenji.html',methods=['POST','GET'])
def checkshenji():
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().chanplimit != 1:
			return render_template('error.html')

		build_server=[]
		serverices_name = request.form.getlist('service_choice')
		up_note = request.form.get('note')
		for i in serverices_name:
			a={}
			static = t_log.query.filter(t_log.id == i).first()
			static.static = 5
			static.update_time = int(time.time())
			db.session.commit()
			a['build_static'] = u'%s 已经验收通过，等待审批上线' % i
	return render_template('shenji.html', static=build_server)

@app.route('/testbuild.html',methods=['POST','GET'])
def testbuild():
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().testlimit != 1:
			return render_template('error.html')

		db_logs = t_log.query.filter(t_log.static != 15).all()

		##########状态判断
		for i in db_logs:
			i.status = status_ck[i.static]
			i.class_status = class_status[i.static]

			i.username=t_user.query.filter(t_user.id ==i.user_id).first().username

			i.uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.update_time))
			i.uppro = u'未上线'

		return render_template('build.html' ,db_logs=db_logs,html_page='shenji.html')

	else:
		return redirect('/login.html')

@app.route('/checkok.html',methods=['POST','GET'])
def checkok():
	###测试完成审计
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().chanplimit != 1:
			return render_template('error.html')

		db_logs = t_log.query.filter(t_log.static == 3).all()

		##########状态判断
		for i in db_logs:
			i.status = status_ck[i.static]
			i.class_status = class_status[i.static]

			i.username=t_user.query.filter(t_user.id ==i.user_id).first().username

			i.uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.update_time))
			i.uppro = u'未上线'

		return render_template('build.html' ,db_logs=db_logs,html_page='checkshenji.html')

	else:
		return redirect('/login.html')

@app.route('/releaseok.html',methods=['POST','GET'])
def releaseok():
	###测试完成审计
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().releaselimit != 1:
			return render_template('error.html')

		db_logs = t_log.query.filter(t_log.static == 4).all()

		##########状态判断
		for i in db_logs:
			i.status = status_ck[i.static]
			i.class_status = class_status[i.static]

			i.username=t_user.query.filter(t_user.id ==i.user_id).first().username

			i.uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.update_time))
			i.uppro = u'未上线'

		return render_template('build.html' ,db_logs=db_logs,html_page='proshenji.html')

	else:
		return redirect('/login.html')

@app.route('/<fileurl>.html')
def viewhtml(fileurl):
	return render_template(fileurl+'.html',services=ArgInput.all_arg)

@app.route('/admin/<fileurl>.html')
def renzhen(fileurl):
	if session['group_id'] == 1:
		return render_template('admin/'+fileurl+'.html')
	else:
		return render_template('error.html')

if __name__ == '__main__':
	server = pywsgi.WSGIServer(('0.0.0.0', 9080), app)
	server.serve_forever()
