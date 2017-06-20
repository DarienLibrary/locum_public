import pymysql

from django.conf import settings


class Database(object):
    _connection = None
    _cursor = None
    
    def __init__(self):
        self._server = settings.ENVISIONWARE['server']
        self._user = settings.ENVISIONWARE['db_user']
        self._password = settings.ENVISIONWARE['db_password']
        self._database = settings.ENVISIONWARE['db_name']
        self._port = settings.ENVISIONWARE['db_port']
        self._connection = pymysql.connect(self._server,
                                           self._user,
                                           self._password,
                                           self._database,
                                           port=self._port)
        self._cursor = self._connection.cursor()

    def __del__(self):
        self._connection.close()

    def query(self, query, params=None):
        self._cursor.execute(query, params)
        results = self._cursor.fetchall()
        return results

    def get_balance(self, patron_barcode):
        query = """
                SELECT actCashBal
                FROM dbauthentication.tbluseracct
                WHERE actUserID = %s"""
        params = patron_barcode
        result = self.query(query, params)
        if result:
            return result[0][0]
