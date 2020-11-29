from mysql import connector

class Database:
    def __init__(self, host, port, database, username, password):
        connection = connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            autocommit=True
        )
        
        self.cursor = connection.cursor(dictionary=True)
    
    def getCursor(self):
        return self.cursor

    def query(self, sql, values):
        self.cursor.execute(sql, values)
        return self.cursor.fetchall()

    def command(self, sql, values):
        self.cursor.execute(sql, values)

class DatabaseFactory:
    @staticmethod
    def create(host, port, database, username, password):
        return Database(host, port, database, username, password)