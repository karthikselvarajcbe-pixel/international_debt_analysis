import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rndsoft@12345",   # 🔴 change this
        database="international_debt_analysis_2"
    )
