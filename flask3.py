#encoding: utf-8
from flask import Flask,redirect,url_for,render_template,request,session
from flask_sqlalchemy import SQLAlchemy
#from celery import Celery
import os,socket,time
import config,ArgInput
from gevent import monkey
from gevent import pywsgi
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
	pro_name = db.Column(db.String(20),nullable=True)
	note = db.Column(db.Text,nullable=True)
	update_time = db.Column(db.Integer)
	uppro_time = db.Column(db.Integer)
	#######状态=1 开发提交 2 测试审计 3 测试通过 4 发布上线 5 已上线
	static = db.Column(db.Integer)

db.create_all()

#add_user=t_user(username='hexiao',password='test123456',group_id='1')
#add_t_log=t_log(user_id=session['user_id'],pro_name=,note=,update_time=,static=)

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


				return redirect('service.html')
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
		return render_template('index.html',services=ArgInput.all_arg,baseserver=ArgInput.base_arg,
							   jarserver=ArgInput.jar_arg)
	else:
		return redirect('/login.html')

@app.route('/pro_static.html',methods=['POST','GET'])
def pro_static():
	if 'username' in session:
		if request.method == 'POST':
			serverices_name = request.form.getlist('service_choice')
			up_note = request.form.get('note')
			for i in serverices_name:

				date_time=time.localtime(time.time())
				add_t_log = t_log(user_id=session['user_id'], pro_name=i, note=up_note, update_time=int(time.time()), static=1)
				db.session.add(add_t_log)
				db.session.commit()

		db_logs = t_log.query.order_by(t_log.static).all()

		##########状态判断
		for i in db_logs:
			if i.static == 1:
				i.status = u"测试审批中"
				i.class_status = u'label-warning'
			elif i.static == 2:
				i.status = u"预发布编译中"
				i.class_status = u'label-danger'
			elif i.static == 3:
				i.status = u"预发布已编译"
				i.class_status = u'label-warning'
			elif i.static == 4:
				i.status = u"生产上线中"
				i.class_status = u'label-danger'
			elif i.static == 5:
				i.status = u"生产已上线"
				i.class_status = u'label-info'
			elif i.static == 14:
				i.status = u"预发布编译失败"
				i.class_status = u'label-danger'

			i.username=t_user.query.filter(t_user.id ==i.user_id).first().username

			i.uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.update_time))

			i.uppro = u'未上线'

		return render_template('pro_static.html' ,db_logs=db_logs)

	else:
		return redirect('/login.html')

###########预发布审计
@app.route('/shenji.html',methods=['POST','GET'])
def shenji():
	if 'username' in session:
		build_server=[]
		for i in request.form.getlist('service_choies'):
			######更新状态
			static = t_log.query.filter(t_log.id == i).first()
			static.static = 2

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
			else:
				ArgInput.build_pro(static.pro_name)

			# ArgInput.uniq_tomcat(static.pro_name)
			i = {}
			i['update_file']=ArgInput.update_file
			print i['update_file']
			if ArgInput.build_static:
				i['build_static']=(u'%s 编译成功' % static.pro_name)
				static.static = 3
				db.session.commit()
			else:
				i['build_static']=(u'%s 编译失败' % static.pro_name)
				i['error_log']=ArgInput.error_log
				static.static = 14
				db.session.commit()

			print i['build_static']
		#########重启预发布
		# list_tomcat1 = set(ArgInput.list_tomcat)
		# for y in list_tomcat1:
		# 	ArgInput.restart_pro(y)
	


			build_server.append(i)
		return render_template('shenji.html' ,static=build_server)

#########生产审计
@app.route('/proshenji.html',methods=['POST','GET'])
def proshenji():
	if 'username' in session:

		for i in request.form.getlist('service_choies'):
			######更新状态
			static = t_log.query.filter(t_log.id == i).first()
			static.static = 4

			db.session.commit()
		#########同步生产
		for i in request.form.getlist('service_choies'):
			static = t_log.query.filter(t_log.id == i).first()
			src_path=os.popen('find /home/rrjctomcat/%s |grep %s\. ' % (ArgInput.local_time,static.pro_name)).read().split('\n')[0]
			if src_path == '':
				print(u'今天没有发布过 %s 项目' % i)
			else:
				os.system('ansible-playbook /home/ansible/service/%s.yml -e  "service_name=%s  src_file=%s  local_time=%s" '% (static.pro_name,static.pro_name,src_path,local_time) )

			static.static = 5
			db.session.commit()

		return render_template('shenji.html')

@app.route('/testbuild.html',methods=['POST','GET'])
def devbuild():
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().testlimit != 1:
			return render_template('error.html')
		if request.method == 'POST':
			serverices_name = request.form.getlist('service_choice')
			up_note = request.form.get('note')
			for i in serverices_name:

				date_time=time.localtime(time.time())
				add_t_log = t_log(user_id=session['user_id'], pro_name=i, note=up_note, update_time=int(time.time()), static=1)
				db.session.add(add_t_log)
				db.session.commit()

		db_logs = t_log.query.filter(t_log.static == 1).all()

		##########状态判断
		for i in db_logs:
			i.status=u'测试审批中'

			i.username=t_user.query.filter(t_user.id ==i.user_id).first().username

			i.uptime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.update_time))
			i.uppro = u'未上线'

		return render_template('build.html' ,db_logs=db_logs,html_page='shenji.html')

	else:
		return redirect('/login.html')

@app.route('/releaseok.html',methods=['POST','GET'])
def releaseok():
	if 'username' in session:
		if t_group.query.filter(t_group.id == session['group_id']).first().releaselimit != 1:
			return render_template('error.html')
		if request.method == 'POST':
			serverices_name = request.form.getlist('service_choice')
			up_note = request.form.get('note')
			for i in serverices_name:

				date_time=time.localtime(time.time())
				add_t_log = t_log(user_id=session['user_id'], pro_name=i, note=up_note, update_time=int(time.time()), static=1)
				db.session.add(add_t_log)
				db.session.commit()

		db_logs = t_log.query.filter(t_log.static == 3).all()

		##########状态判断
		for i in db_logs:
			i.status=u'预发布已编译'

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
#	app.run(port=9080,host='0.0.0.0')
	server = pywsgi.WSGIServer(('0.0.0.0', 9080), app)
	server.serve_forever()
