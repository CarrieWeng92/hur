import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("錯誤：找不到 DATABASE_URL")
    exit()

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

try:
    print("正在檢查並建立資料表...")
    
    # 1. 建立 hur_members 表 (HUR+ 成員資訊)
    create_members_table = """
    CREATE TABLE IF NOT EXISTS hur_members (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        filename VARCHAR(255) NOT NULL,
        intro TEXT
    );
    """
    cursor.execute(create_members_table)

    # 2. 建立 user_logs 表 (新增的部分：用來存對話紀錄)
    create_logs_table = """
    CREATE TABLE IF NOT EXISTS user_logs (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_logs_table)
    
    # 3. 檢查成員資料是否需要寫入
    cursor.execute("SELECT COUNT(*) FROM hur_members;")
    if cursor.fetchone()[0] == 0:
        print("正在寫入 HUR+ 成員資料...")
        members_data = [
            ('利善榛', 'cindy.png', '1995年3月18日\nLeader、Sub-Vocal、Visual'),
            ('裴頡', 'jasmine.png', '1997年3月13日\nLead Vocal、Center'),
            ('C.HOLLY', 'cholly.png', '1998年3月24日\nMain Rapper、Lead Dancer'),
            ('連穎', 'erin.png', '1999年4月27日\nMain Dancer、Sub-Vocal'),
            ('巴倫月', 'sizi.png', '1999年5月12日\nMain Vocal'),
            ('席子淇', 'jennifer.png', '2000年8月15日\nSub-Vocal、Sub-Dancer'),
            ('佟凱玲', 'shannon.png', '1999年1月14日\nSub-Vocal、Sub-Dancer'),
            ('林詩雅', 'grace.png', '1999年1月13日\nSub-Vocal、Sub-Dancer'),
            ('香蘭', 'lanlan.png', '2008年3月13日\nSub-Vocal、Maknae')
        ]
        cursor.executemany("INSERT INTO hur_members (name, filename, intro) VALUES (%s, %s, %s)", members_data)
        print("成員資料寫入完成。")

    conn.commit()
    print("資料庫所有表格初始化完成！")

except Exception as e:
    print("發生錯誤：", e)
    conn.rollback()

finally:
    cursor.close()
    conn.close()
