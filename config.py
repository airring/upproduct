dialect='mysql'
driver='mysqldb'
username='pd'
password='test123456'
host='192.168.3.105'
port='3306'
database='uppor'


#dialect+driver://username:password@host:port/database
SQLALCHEMY_DATABASE_URI="{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(dialect,driver,username,password,host,port,database)
SQLALCHEMY_TRACK_MODIFICATIONS = False