import psycopg2

# Thay đổi các thông tin kết nối dựa trên cài đặt của bạn
db_params = {
    "host": "103.75.187.211",
    "port": "5432",
    "database": "bcent",
    "user": "cuns",
    "password": "cuns251021@"
}

# Kết nối đến cơ sở dữ liệu
connection = psycopg2.connect(**db_params)
cursor = connection.cursor()



